"""SVG renderer: semantic model + layout -> SVG text.

Connectivity is shown with net labels next to each pin, not drawn
wires — see requirements section 11 (net labels are an explicitly
valid substitute for long/messy physical wires) and section 17 (the
renderer must not determine electrical connectivity, only draw what
the model and layout already decided). Real wire routing between
nearby pins is stage 5, on top of this.
"""

from __future__ import annotations

from html import escape

from schematic.layout import SchematicLayout
from schematic.model import Schematic

STUB_LENGTH = 16
FONT_FAMILY = "monospace"


def _build_node_to_net(schematic: Schematic) -> dict[str, str]:
    node_to_net = {}
    for net in schematic.nets.values():
        for node in net.nodes:
            node_to_net[node] = net.name
    return node_to_net


def render_svg(schematic: Schematic, layout: SchematicLayout) -> str:
    node_to_net = _build_node_to_net(schematic)
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {layout.width:.0f} {layout.height:.0f}" '
        f'width="{layout.width:.0f}" height="{layout.height:.0f}" '
        f'font-family="{FONT_FAMILY}">',
        '<rect x="0" y="0" width="100%" height="100%" fill="white"/>',
    ]

    for component in schematic.components.values():
        box = layout.boxes[component.id]
        parts.append(
            f'<rect x="{box.x:.0f}" y="{box.y:.0f}" width="{box.width:.0f}" '
            f'height="{box.height:.0f}" fill="none" stroke="black" stroke-width="1.5"/>'
        )

        title = component.label or component.reference or component.id
        parts.append(
            f'<text x="{box.x + box.width / 2:.0f}" y="{box.y - 8:.0f}" '
            f'text-anchor="middle" font-size="13" font-weight="bold">{escape(title)}</text>'
        )
        if component.value:
            parts.append(
                f'<text x="{box.x + box.width / 2:.0f}" y="{box.y + box.height + 14:.0f}" '
                f'text-anchor="middle" font-size="11" fill="#555">{escape(component.value)}</text>'
            )

        for pin in component.pins:
            if pin.hidden:
                continue
            pin_pos = box.pins.get(pin.number)
            if pin_pos is None:
                continue

            if pin_pos.side == "left":
                stub_x2 = pin_pos.x - STUB_LENGTH
                name_x, name_anchor = stub_x2 - 4, "end"
                num_x, num_anchor = box.x + 4, "start"
                label_x, label_anchor = stub_x2 - 4, "end"
                label_y_offset = -4
            else:
                stub_x2 = pin_pos.x + STUB_LENGTH
                name_x, name_anchor = stub_x2 + 4, "start"
                num_x, num_anchor = box.x + box.width - 4, "end"
                label_x, label_anchor = stub_x2 + 4, "start"
                label_y_offset = -4

            parts.append(
                f'<line x1="{pin_pos.x:.0f}" y1="{pin_pos.y:.0f}" '
                f'x2="{stub_x2:.0f}" y2="{pin_pos.y:.0f}" stroke="black" stroke-width="1"/>'
            )
            parts.append(
                f'<text x="{num_x:.0f}" y="{pin_pos.y + 3:.0f}" text-anchor="{num_anchor}" '
                f'font-size="9" fill="#888">{escape(pin.number)}</text>'
            )
            parts.append(
                f'<text x="{name_x:.0f}" y="{pin_pos.y + 3:.0f}" text-anchor="{name_anchor}" '
                f'font-size="11">{escape(pin.name)}</text>'
            )

            net_name = node_to_net.get(f"{component.id}.{pin.number}")
            if net_name:
                parts.append(
                    f'<text x="{label_x:.0f}" y="{pin_pos.y + label_y_offset:.0f}" '
                    f'text-anchor="{label_anchor}" font-size="9" fill="#2a6" '
                    f'font-style="italic">{escape(net_name)}</text>'
                )

    parts.append("</svg>")
    return "\n".join(parts)
