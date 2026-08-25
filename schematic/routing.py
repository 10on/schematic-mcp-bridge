"""Orthogonal wire routing for every 2-endpoint net.

Two strategies, in order of preference:

1. Direct route — the two components are immediate row neighbors and
   their pins face each other (left box's pin on its right edge, right
   box's pin on its left edge). Cheapest, cleanest-looking case.
2. Channel route — everything else. Drops from the source pin down
   into a shared horizontal channel below the whole row, travels to
   the target's x, then rises into the target pin. Each such wire gets
   its own lane in the channel so parallel long-distance wires don't
   overlap. This deliberately doesn't try to minimize crossings or
   total wire length — a real router (ELK etc.) is requirements section
   18 / stage 7 territory if this turns out not to be good enough.

A net with 3+ endpoints (a bus) or fewer than 2 (documents pin intent
only) is never routed as a wire — see renderer.py / section 11 on net
labels for those.
"""

from __future__ import annotations

from dataclasses import dataclass

from schematic.layout import STUB_LENGTH, PinPosition, SchematicLayout
from schematic.model import Schematic

CHANNEL_MARGIN = 20
LANE_GAP = 12


@dataclass
class Wire:
    net_name: str
    node_a: str
    node_b: str
    points: list[tuple[float, float]]


def _stub_end(pin_pos: PinPosition) -> tuple[float, float]:
    dx = -STUB_LENGTH if pin_pos.side == "left" else STUB_LENGTH
    return (pin_pos.x + dx, pin_pos.y)


def _direct_route(
    comp_a: str, pos_a: PinPosition, comp_b: str, pos_b: PinPosition, order_index: dict[str, int]
) -> list[tuple[float, float]] | None:
    if order_index[comp_a] < order_index[comp_b]:
        left_pos, right_pos = pos_a, pos_b
    else:
        left_pos, right_pos = pos_b, pos_a
    if left_pos.side != "right" or right_pos.side != "left":
        return None  # pins don't face each other; a straight route would cross a box

    start, end = _stub_end(left_pos), _stub_end(right_pos)
    if start[1] == end[1]:
        return [start, end]
    mid_x = (start[0] + end[0]) / 2
    return [start, (mid_x, start[1]), (mid_x, end[1]), end]


def _channel_route(
    pos_a: PinPosition, pos_b: PinPosition, lane_y: float
) -> list[tuple[float, float]]:
    start, end = _stub_end(pos_a), _stub_end(pos_b)
    return [start, (start[0], lane_y), (end[0], lane_y), end]


def route_wires(schematic: Schematic, layout: SchematicLayout) -> list[Wire]:
    order = list(layout.boxes)
    order_index = {component_id: i for i, component_id in enumerate(order)}
    neighbor_pairs = {frozenset((a, b)) for a, b in zip(order, order[1:])}
    channel_y = max((box.y + box.height for box in layout.boxes.values()), default=0.0) + CHANNEL_MARGIN

    wires: list[Wire] = []
    lanes_used = 0
    for net in schematic.nets.values():
        if len(net.nodes) != 2:
            continue
        node_a, node_b = net.nodes
        comp_a, pin_a = node_a.split(".", 1)
        comp_b, pin_b = node_b.split(".", 1)
        if comp_a == comp_b or comp_a not in layout.boxes or comp_b not in layout.boxes:
            continue
        pos_a = layout.boxes[comp_a].pins.get(pin_a)
        pos_b = layout.boxes[comp_b].pins.get(pin_b)
        if pos_a is None or pos_b is None:
            continue

        points = None
        if frozenset((comp_a, comp_b)) in neighbor_pairs:
            points = _direct_route(comp_a, pos_a, comp_b, pos_b, order_index)
        if points is None:
            points = _channel_route(pos_a, pos_b, channel_y + lanes_used * LANE_GAP)
            lanes_used += 1

        wires.append(Wire(net_name=net.name, node_a=node_a, node_b=node_b, points=points))

    return wires
