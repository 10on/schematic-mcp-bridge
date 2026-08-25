"""Direct orthogonal wire routing for the simple, safe case.

A wire is only drawn between two components that ended up as immediate
neighbors in the row layout, for a net with exactly two endpoints, with
pins facing each other (left box's pin on its right edge, right box's
pin on its left edge) — routing between non-adjacent components would
have to detour around whatever box sits in between, which is real
routing-algorithm territory (see requirements section 18, deferred to
stage 7 if this turns out not to be enough). Every other connection
stays a net label (renderer.py), matching section 11's own guidance to
prefer labels over messy physical wires.
"""

from __future__ import annotations

from dataclasses import dataclass

from schematic.layout import STUB_LENGTH, SchematicLayout
from schematic.model import Schematic


@dataclass
class Wire:
    net_name: str
    node_a: str
    node_b: str
    points: list[tuple[float, float]]


def _stub_end(pin_pos, side: str) -> tuple[float, float]:
    dx = -STUB_LENGTH if side == "left" else STUB_LENGTH
    return (pin_pos.x + dx, pin_pos.y)


def route_wires(schematic: Schematic, layout: SchematicLayout) -> list[Wire]:
    order = list(layout.boxes)
    order_index = {component_id: i for i, component_id in enumerate(order)}
    neighbor_pairs = {
        frozenset((a, b)) for a, b in zip(order, order[1:])
    }

    wires: list[Wire] = []
    for net in schematic.nets.values():
        if len(net.nodes) != 2:
            continue
        node_a, node_b = net.nodes
        comp_a, pin_a = node_a.split(".", 1)
        comp_b, pin_b = node_b.split(".", 1)
        if comp_a == comp_b or frozenset((comp_a, comp_b)) not in neighbor_pairs:
            continue

        if order_index[comp_a] < order_index[comp_b]:
            left_id, left_pin, right_id, right_pin, left_node, right_node = (
                comp_a, pin_a, comp_b, pin_b, node_a, node_b,
            )
        else:
            left_id, left_pin, right_id, right_pin, left_node, right_node = (
                comp_b, pin_b, comp_a, pin_a, node_b, node_a,
            )

        left_pos = layout.boxes[left_id].pins.get(left_pin)
        right_pos = layout.boxes[right_id].pins.get(right_pin)
        if left_pos is None or right_pos is None:
            continue
        if left_pos.side != "right" or right_pos.side != "left":
            continue  # pins don't face each other; a straight route would cross a box

        start = _stub_end(left_pos, "right")
        end = _stub_end(right_pos, "left")
        if start[1] == end[1]:
            points = [start, end]
        else:
            mid_x = (start[0] + end[0]) / 2
            points = [start, (mid_x, start[1]), (mid_x, end[1]), end]

        wires.append(Wire(net_name=net.name, node_a=left_node, node_b=right_node, points=points))

    return wires
