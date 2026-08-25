"""KiCad symbol library import, backed by SKiDL.

Normalizes real `.kicad_sym` library data into the `Component`/`Pin`
shapes from `schematic.model`, so the rest of the system never has to
know about KiCad's symbol file format. See requirements section 15.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import skidl

from schematic.model import Component, Pin

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LIB_DIRS = [REPO_ROOT / "tests" / "fixtures" / "kicad-symbols"]

PIN_FUNC_TO_ELECTRICAL_TYPE = {
    1: "input",
    2: "output",
    3: "bidirectional",
    4: "tri_state",
    5: "passive",
    6: "unspecified",
    7: "power_in",
    8: "power_out",
    9: "open_collector",
    10: "open_emitter",
    11: "pull_up",
    12: "pull_down",
    13: "no_connect",
    14: "free",
}


class ComponentNotInLibraryError(Exception):
    pass


@dataclass
class ComponentSearchResult:
    library_id: str
    description: str
    keywords: str
    ref_prefix: str


def _fix_mojibake(text: str) -> str:
    """SKiDL reads .kicad_sym files as Latin-1, mangling non-ASCII UTF-8
    text (e.g. '±', 'µ', 'Ω') into two-character garbage. Undo that."""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def _split_library_id(library_id: str) -> tuple[str, str]:
    if ":" not in library_id:
        raise ValueError(f"invalid library_id '{library_id}', expected 'Library:Symbol'")
    lib_name, symbol_name = library_id.split(":", 1)
    return lib_name, symbol_name


class ComponentLibrary:
    """Searches and imports components from a directory of `.kicad_sym` files."""

    def __init__(self, search_paths: list[str | Path], tool: int = skidl.KICAD9):
        self.tool = tool
        self.search_paths = [str(p) for p in search_paths]
        skidl.lib_search_paths[tool] = list(self.search_paths)
        self._schlib_cache: dict[str, skidl.SchLib] = {}

    def _lib_names(self) -> list[str]:
        names = []
        for search_path in self.search_paths:
            for path in Path(search_path).glob("*.kicad_sym"):
                names.append(path.stem)
        return sorted(set(names))

    def _load_schlib(self, lib_name: str) -> skidl.SchLib:
        if lib_name not in self._schlib_cache:
            self._schlib_cache[lib_name] = skidl.SchLib(lib_name, tool=self.tool)
        return self._schlib_cache[lib_name]

    def _find_skidl_part(self, library_id: str) -> skidl.Part:
        """Returns a fully-parsed part — fields like ref_prefix/value are
        wrong defaults (e.g. ref_prefix is always 'U') until parse() runs."""
        lib_name, symbol_name = _split_library_id(library_id)
        schlib = self._load_schlib(lib_name)
        for part in schlib.parts:
            if part.name == symbol_name:
                part.parse()
                return part
        raise ComponentNotInLibraryError(f"'{symbol_name}' not found in library '{lib_name}'")

    def search_components(self, query: str) -> list[ComponentSearchResult]:
        """Case-insensitive substring match against symbol name, description, keywords."""
        needle = query.lower()
        results = []
        for lib_name in self._lib_names():
            schlib = self._load_schlib(lib_name)
            for part in schlib.parts:
                haystack = " ".join(
                    filter(None, [part.name, part.description, part.keywords])
                ).lower()
                if needle in haystack:
                    # name/description/keywords are already correct pre-parse,
                    # but ref_prefix is a placeholder ('U') until parsed —
                    # only pay for parsing once we know it's a match.
                    part.parse()
                    results.append(
                        ComponentSearchResult(
                            library_id=f"{lib_name}:{part.name}",
                            description=_fix_mojibake(part.description or ""),
                            keywords=_fix_mojibake(part.keywords or ""),
                            ref_prefix=part.ref_prefix,
                        )
                    )
        return results

    def get_component(self, library_id: str) -> dict:
        part = self._find_skidl_part(library_id)
        pins = self.get_component_pins(library_id)
        return {
            "library_id": library_id,
            "description": _fix_mojibake(part.description or ""),
            "ref_prefix": part.ref_prefix,
            "pins": [pin.to_dict() for pin in pins],
        }

    def get_component_pins(self, library_id: str) -> list[Pin]:
        part = self._find_skidl_part(library_id)
        return [
            Pin(
                number=str(pin.num),
                name=_fix_mojibake(pin.name),
                electrical_type=PIN_FUNC_TO_ELECTRICAL_TYPE.get(int(pin.func), "unspecified"),
            )
            for pin in part.pins
        ]

    def instantiate(
        self,
        library_id: str,
        component_id: str,
        value: str | None = None,
        reference: str | None = None,
        label: str | None = None,
    ) -> Component:
        """Build a standalone `Component` from a library symbol (not yet added to a schematic).

        `reference` defaults to `component_id`, not the library's bare
        ref_prefix ('R', 'C', ...) — the prefix alone isn't a unique
        reference designator, so leaving it as the default silently
        produces duplicate_reference errors as soon as a second part
        from the same library symbol gets added.
        """
        part = self._find_skidl_part(library_id)
        return Component(
            id=component_id,
            library_id=library_id,
            reference=reference or component_id,
            value=value if value is not None else (part.value or None),
            label=label,
            pins=self.get_component_pins(library_id),
            metadata={"description": _fix_mojibake(part.description or "")},
        )
