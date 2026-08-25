"""Stateful session implementing the tool API from requirements section 8.

Framework-free on purpose: `MCPServer` in `server.py` just binds each
method here to an MCP tool. Keeping the logic here means it's testable
without spinning up a real MCP server, and the same session could be
driven by something other than MCP later.

One `SchematicSession` holds at most one active schematic, matching the
conversational workflow in section 2/3: an agent creates or loads a
schematic, edits it over several tool calls, then renders/saves it.
"""

from __future__ import annotations

from dataclasses import asdict

from schematic.layout import SchematicLayout, auto_layout as auto_layout_fn
from schematic.library import DEFAULT_LIB_DIRS, ComponentLibrary
from schematic.model import ComponentNotFoundError, Schematic
from schematic.renderer import render_svg as render_svg_fn
from schematic.validation import run_erc as run_erc_fn
from schematic.validation import validate as validate_fn


class NoActiveSchematicError(Exception):
    pass


class SchematicSession:
    def __init__(self, lib_search_paths=None):
        self.library = ComponentLibrary(search_paths=lib_search_paths or DEFAULT_LIB_DIRS)
        self.schematic: Schematic | None = None
        self._layout: SchematicLayout | None = None

    def _require_schematic(self) -> Schematic:
        if self.schematic is None:
            raise NoActiveSchematicError(
                "no active schematic — call create_schematic or load_schematic first"
            )
        return self.schematic

    def _require_component(self, schematic: Schematic, component_id: str):
        component = schematic.components.get(component_id)
        if component is None:
            raise ComponentNotFoundError(f"unknown component '{component_id}'")
        return component

    def _invalidate_layout(self) -> None:
        self._layout = None

    # -- library ----------------------------------------------------------

    def search_components(self, query: str) -> list[dict]:
        return [asdict(r) for r in self.library.search_components(query)]

    def get_component(self, library_id: str) -> dict:
        return self.library.get_component(library_id)

    def get_component_pins(self, library_id: str) -> list[dict]:
        return [pin.to_dict() for pin in self.library.get_component_pins(library_id)]

    # -- schematic lifecycle ------------------------------------------------

    def create_schematic(self, name: str) -> dict:
        self.schematic = Schematic(name=name)
        self._invalidate_layout()
        return {"name": name}

    def load_schematic(self, path: str) -> dict:
        self.schematic = Schematic.load(path)
        self._invalidate_layout()
        return {
            "name": self.schematic.name,
            "components": len(self.schematic.components),
            "nets": len(self.schematic.nets),
        }

    def save_schematic(self, path: str) -> dict:
        self._require_schematic().save(path)
        return {"saved": path}

    # -- schematic editing --------------------------------------------------

    def add_component(
        self,
        library_id: str,
        component_id: str,
        reference: str | None = None,
        value: str | None = None,
        label: str | None = None,
    ) -> dict:
        schematic = self._require_schematic()
        component = self.library.instantiate(
            library_id, component_id, value=value, reference=reference, label=label
        )
        schematic.add_component(component)
        self._invalidate_layout()
        return component.to_dict()

    def remove_component(self, component_id: str) -> dict:
        schematic = self._require_schematic()
        schematic.remove_component(component_id)
        self._invalidate_layout()
        return {"removed": component_id}

    def set_component_value(self, component_id: str, value: str) -> dict:
        schematic = self._require_schematic()
        component = self._require_component(schematic, component_id)
        component.value = value
        return component.to_dict()

    # -- connections ----------------------------------------------------

    def connect(self, pin_a: str, pin_b: str) -> dict:
        net_name = self._require_schematic().connect(pin_a, pin_b)
        return {"net": net_name}

    def connect_net(self, net_name: str, pins: list[str]) -> dict:
        return {"net": self._require_schematic().connect_net(net_name, pins)}

    def disconnect(self, pin: str) -> dict:
        self._require_schematic().disconnect(pin)
        return {"disconnected": pin}

    def rename_net(self, old_name: str, new_name: str) -> dict:
        self._require_schematic().rename_net(old_name, new_name)
        return {"renamed_to": new_name}

    # -- layout -------------------------------------------------------------
    # set_placement_hint/set_pin_side/group_components store intent on the
    # model. auto_layout() (stage 3, naive row placement) is the only thing
    # that currently consumes any of it, and it doesn't yet — real placement
    # heuristics are stage 5.

    def set_placement_hint(self, component_id: str, relation: str, target: str) -> dict:
        schematic = self._require_schematic()
        component = self._require_component(schematic, component_id)
        component.placement_hint = {"relation": relation, "target": target}
        return component.to_dict()

    def set_pin_side(self, component_id: str, pin: str, side: str) -> dict:
        schematic = self._require_schematic()
        component = self._require_component(schematic, component_id)
        pin_obj = component.get_pin(pin)
        pin_obj.side = side
        return pin_obj.to_dict()

    def group_components(self, group_name: str, component_ids: list[str]) -> dict:
        schematic = self._require_schematic()
        for component_id in component_ids:
            component = self._require_component(schematic, component_id)
            component.metadata["group"] = group_name
        return {"group": group_name, "components": component_ids}

    def auto_layout(self) -> dict:
        schematic = self._require_schematic()
        self._layout = auto_layout_fn(schematic)
        return {
            "width": self._layout.width,
            "height": self._layout.height,
            "components": len(self._layout.boxes),
        }

    # -- validation -----------------------------------------------------

    def validate(self) -> dict:
        return validate_fn(self._require_schematic())

    def run_erc(self) -> dict:
        return run_erc_fn(self._require_schematic())

    # -- output -----------------------------------------------------------

    def render_svg(self) -> dict:
        schematic = self._require_schematic()
        if self._layout is None:
            self._layout = auto_layout_fn(schematic)
        return {"svg": render_svg_fn(schematic, self._layout)}

    def get_preview(self) -> dict:
        return self.render_svg()

    def export_kicad(self) -> dict:
        raise NotImplementedError("KiCad export is not implemented yet (stage 6)")
