"""`.kicad_sch` export, backed by SKiDL's schematic generator.

Requirements section 19 explicitly prefers this over hand-rolling a
KiCad file writer: SKiDL already draws real classical symbols (see
section 16) with correct pin geometry, which is a lot more work to
reimplement than to reuse. This is an optional backend on top of the
semantic model — nothing else in the system depends on it, and it only
works for components that came from a real library symbol (`add_component`
via `schematic/library.py`), since there's no real KiCad symbol to draw
for a hand-authored/invented component.
"""

from __future__ import annotations

from pathlib import Path

import skidl

from schematic.library import DEFAULT_LIB_DIRS
from schematic.model import Schematic


class KicadExportError(Exception):
    pass


def export_kicad(
    schematic: Schematic,
    output_path: str | Path,
    lib_search_paths: list[str | Path] | None = None,
) -> Path:
    output_path = Path(output_path)
    skidl.lib_search_paths[skidl.KICAD9] = [str(p) for p in (lib_search_paths or DEFAULT_LIB_DIRS)]

    circuit = skidl.Circuit()
    skidl_parts: dict[str, skidl.Part] = {}
    for component in schematic.components.values():
        if ":" not in component.library_id:
            raise KicadExportError(
                f"component '{component.id}' has no real library symbol "
                f"(library_id='{component.library_id}') — can't export to KiCad"
            )
        lib_name, symbol_name = component.library_id.split(":", 1)
        try:
            skidl_parts[component.id] = skidl.Part(
                lib_name,
                symbol_name,
                ref=component.id,
                value=component.value or "",
                tool=skidl.KICAD9,
                circuit=circuit,
            )
        except Exception as exc:  # SKiDL raises a mix of its own + generic errors
            raise KicadExportError(
                f"component '{component.id}': couldn't load '{component.library_id}' "
                f"from the KiCad library — {exc}"
            ) from exc

    for net in schematic.nets.values():
        skidl_net = skidl.Net(net.name, circuit=circuit)
        for node in net.nodes:
            component_id, pin_number = node.split(".", 1)
            skidl_net += skidl_parts[component_id][pin_number]

    circuit.generate_schematic(
        filepath=str(output_path.parent or "."), top_name=output_path.stem, title=schematic.name
    )

    generated = (output_path.parent or Path(".")) / f"{output_path.stem}.kicad_sch"
    if generated != output_path:
        generated.replace(output_path)
    return output_path
