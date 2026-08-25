"""Naive automatic layout: one row of component boxes, left to right.

This is deliberately simple — real placement heuristics (signal flow
left-to-right, power rails on top, grouping related parts, ELK-based
placement) are requirements section 10 / stage 5, not this stage. This
module only has to produce *some* non-overlapping, deterministic
geometry so the renderer has coordinates to draw.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from schematic.model import Schematic

PIN_SPACING = 24
BOX_PADDING_Y = 20
BOX_MIN_WIDTH = 140
COMPONENT_GAP = 80
CHAR_WIDTH = 7
ROW_Y = 60


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


def auto_layout(schematic: Schematic) -> SchematicLayout:
    boxes: dict[str, ComponentBox] = {}
    cursor_x = COMPONENT_GAP
    max_bottom = 0.0

    for component in schematic.components.values():
        visible_pins = [p for p in component.pins if not p.hidden]
        split = (len(visible_pins) + 1) // 2
        left_pins, right_pins = visible_pins[:split], visible_pins[split:]
        rows = max(len(left_pins), len(right_pins), 1)
        height = rows * PIN_SPACING + BOX_PADDING_Y * 2

        longest_label = max((len(p.name) for p in visible_pins), default=0)
        width = max(BOX_MIN_WIDTH, longest_label * CHAR_WIDTH * 2 + 60)

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
        cursor_x += width + COMPONENT_GAP
        max_bottom = max(max_bottom, box.y + box.height)

    return SchematicLayout(boxes=boxes, width=cursor_x, height=max_bottom + COMPONENT_GAP)
