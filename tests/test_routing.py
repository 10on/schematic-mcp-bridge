from schematic.layout import auto_layout
from schematic.model import Component, Pin, Schematic
from schematic.routing import route_wires


def two_pin(component_id: str) -> Component:
    return Component(
        id=component_id,
        library_id="Device:R",
        pins=[Pin(number="1", name="1"), Pin(number="2", name="2")],
    )


def test_routes_wire_between_facing_neighbor_pins():
    schematic = Schematic(name="demo")
    schematic.add_component(two_pin("R1"))
    schematic.add_component(two_pin("R2"))
    schematic.connect("R1.2", "R2.1")  # R1's right-side pin to R2's left-side pin

    layout = auto_layout(schematic)
    wires = route_wires(schematic, layout)

    assert len(wires) == 1
    assert {wires[0].node_a, wires[0].node_b} == {"R1.2", "R2.1"}
    assert len(wires[0].points) >= 2


def test_does_not_route_non_facing_pins():
    schematic = Schematic(name="demo")
    schematic.add_component(two_pin("R1"))
    schematic.add_component(two_pin("R2"))
    schematic.connect("R1.1", "R2.1")  # both on the left side — would cross R1's own box

    layout = auto_layout(schematic)
    wires = route_wires(schematic, layout)
    assert wires == []


def test_does_not_route_non_adjacent_components():
    schematic = Schematic(name="demo")
    schematic.add_component(two_pin("R1"))
    schematic.add_component(two_pin("R2"))
    schematic.add_component(two_pin("R3"))
    schematic.connect("R1.2", "R3.1")  # R2 sits physically between them

    layout = auto_layout(schematic)
    wires = route_wires(schematic, layout)
    assert wires == []


def test_does_not_route_nets_with_more_than_two_endpoints():
    schematic = Schematic(name="demo")
    schematic.add_component(two_pin("R1"))
    schematic.add_component(two_pin("R2"))
    schematic.add_component(two_pin("R3"))
    schematic.connect_net("BUS", ["R1.2", "R2.1", "R3.1"])

    layout = auto_layout(schematic)
    wires = route_wires(schematic, layout)
    assert wires == []
