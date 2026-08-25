"""Structural validation and basic ERC. See requirements section 12.

`validate()` checks structural integrity of the schematic (references,
unconnected pins). `run_erc()` builds on it with electrical checks
(output-to-output conflicts, undriven power nets).
"""

from __future__ import annotations

from schematic.model import Component, Pin, Schematic


def _pin_for_node(schematic: Schematic, node: str) -> tuple[Component, Pin] | tuple[None, None]:
    component_id, pin_ref = node.split(".", 1)
    component = schematic.components.get(component_id)
    if component is None:
        return None, None
    for pin in component.pins:
        if pin.number == pin_ref:
            return component, pin
    return None, None


def validate(schematic: Schematic) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []

    references_seen: dict[str, list[str]] = {}
    for component in schematic.components.values():
        if component.reference:
            references_seen.setdefault(component.reference, []).append(component.id)
    for reference, component_ids in references_seen.items():
        if len(component_ids) > 1:
            errors.append(
                {
                    "type": "duplicate_reference",
                    "reference": reference,
                    "components": component_ids,
                }
            )

    connected_nodes = {node for net in schematic.nets.values() for node in net.nodes}
    for component in schematic.components.values():
        for pin in component.pins:
            if pin.hidden:
                continue
            node = f"{component.id}.{pin.number}"
            if node not in connected_nodes:
                warnings.append(
                    {"type": "unconnected_pin", "component": component.id, "pin": pin.number}
                )

    return {"errors": errors, "warnings": warnings}


def run_erc(schematic: Schematic) -> dict:
    result = validate(schematic)
    errors = list(result["errors"])
    warnings = list(result["warnings"])

    for net in schematic.nets.values():
        output_pins = []
        power_in_pins = []
        power_out_pins = []
        for node in net.nodes:
            _, pin = _pin_for_node(schematic, node)
            if pin is None:
                continue
            if pin.electrical_type == "output":
                output_pins.append(node)
            elif pin.electrical_type == "power_in":
                power_in_pins.append(node)
            elif pin.electrical_type == "power_out":
                power_out_pins.append(node)

        if len(output_pins) > 1:
            errors.append({"type": "output_conflict", "net": net.name, "pins": output_pins})

        if power_in_pins and not power_out_pins:
            warnings.append(
                {"type": "power_input_not_driven", "net": net.name, "pins": power_in_pins}
            )

    return {"errors": errors, "warnings": warnings}
