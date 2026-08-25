"""Automatic layout: one row of component boxes, left to right.

Row order honors `left_of`/`right_of` placement hints (requirements
section 10) via a topological sort; other relations (`above`, `below`,
`near`, `same_row`, `same_column`) don't mean anything in a single-row
layout and are ignored — a real 2D layout is stage 7 territory if this
turns out not to be good enough. Grouping (`group_components`) is
still stored-but-unused intent; see mcp_server/tools.py.

The horizontal gap between boxes is sized dynamically from the pin/net
label text each box will draw outward (renderer.py) — a fixed gap
would overlap text whenever labels are longer than expected.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from schematic.model import Component, Pin, Schematic

PIN_SPACING = 24
BOX_PADDING_Y = 20
BOX_MIN_WIDTH = 140
BOX_CHAR_WIDTH = 7
STUB_LENGTH = 16
PIN_NAME_CHAR_WIDTH = 6.8  # renderer draws pin names at font-size 11
NET_LABEL_CHAR_WIDTH = 5.8  # renderer draws net labels at font-size 9
SIDE_MARGIN = 16
ROW_Y = 60
BOTTOM_MARGIN = 40


@dataclass
class PinPosition:
    x: float
    y: float
    side: str  # "left" | "right"


@dataclass
class ComponentBox:
    x: float
    y: float
    width: float
    height: float
    pins: dict[str, PinPosition] = field(default_factory=dict)


@dataclass
class SchematicLayout:
    boxes: dict[str, ComponentBox] = field(default_factory=dict)
    width: float = 0
    height: float = 0


def _side_reach(pins: list[Pin], component_id: str, node_to_net: dict[str, str]) -> float:
    """How far out from the box edge this side's text will extend."""
    if not pins:
        return STUB_LENGTH + SIDE_MARGIN
    widest = 0.0
    for pin in pins:
        name_width = len(pin.name) * PIN_NAME_CHAR_WIDTH
        net_name = node_to_net.get(f"{component_id}.{pin.number}")
        net_width = len(net_name) * NET_LABEL_CHAR_WIDTH if net_name else 0.0
        widest = max(widest, name_width, net_width)
    return STUB_LENGTH + widest + SIDE_MARGIN


def _ordered_components(schematic: Schematic) -> list[Component]:
    """Insertion order, adjusted for left_of/right_of placement hints via a
    stable topological sort. A hint referencing an unknown component, or
    that would create a cycle, is silently ignored (best-effort, never
    raises — a bad hint shouldn't block rendering)."""
    components = list(schematic.components.values())
    order_index = {c.id: i for i, c in enumerate(components)}
    must_precede: dict[str, set[str]] = {c.id: set() for c in components}

    for component in components:
        hint = component.placement_hint
        if not hint or hint.get("target") not in order_index:
            continue
        relation, target = hint.get("relation"), hint["target"]
        if relation == "left_of":
            must_precede[target].add(component.id)
        elif relation == "right_of":
            must_precede[component.id].add(target)

    ordered_ids: list[str] = []
    done: set[str] = set()
    in_progress: set[str] = set()

    def visit(component_id: str) -> None:
        if component_id in done or component_id in in_progress:
            return
        in_progress.add(component_id)
        for dep_id in sorted(must_precede[component_id], key=lambda cid: order_index[cid]):
            visit(dep_id)
        in_progress.discard(component_id)
        done.add(component_id)
        ordered_ids.append(component_id)

    for component in components:
        visit(component.id)

    return [schematic.components[cid] for cid in ordered_ids]


def auto_layout(schematic: Schematic) -> SchematicLayout:
    node_to_net = schematic.node_to_net_map()
    boxes: dict[str, ComponentBox] = {}
    cursor_x = 0.0
    max_bottom = 0.0
    prev_right_reach = 0.0

    for component in _ordered_components(schematic):
        visible_pins = [p for p in component.pins if not p.hidden]
        split = (len(visible_pins) + 1) // 2
        left_pins, right_pins = visible_pins[:split], visible_pins[split:]
        rows = max(len(left_pins), len(right_pins), 1)
        height = rows * PIN_SPACING + BOX_PADDING_Y * 2

        longest_label = max((len(p.name) for p in visible_pins), default=0)
        width = max(BOX_MIN_WIDTH, longest_label * BOX_CHAR_WIDTH * 2 + 60)

        left_reach = _side_reach(left_pins, component.id, node_to_net)
        right_reach = _side_reach(right_pins, component.id, node_to_net)

        cursor_x += prev_right_reach + left_reach
        box = ComponentBox(x=cursor_x, y=ROW_Y, width=width, height=height)
        for i, pin in enumerate(left_pins):
            box.pins[pin.number] = PinPosition(
                x=box.x, y=box.y + BOX_PADDING_Y + i * PIN_SPACING + PIN_SPACING / 2, side="left"
            )
        for i, pin in enumerate(right_pins):
            box.pins[pin.number] = PinPosition(
                x=box.x + box.width,
                y=box.y + BOX_PADDING_Y + i * PIN_SPACING + PIN_SPACING / 2,
                side="right",
            )

        boxes[component.id] = box
        cursor_x += width
        prev_right_reach = right_reach
        max_bottom = max(max_bottom, box.y + box.height)

    total_width = cursor_x + prev_right_reach
    return SchematicLayout(boxes=boxes, width=total_width, height=max_bottom + BOTTOM_MARGIN)
