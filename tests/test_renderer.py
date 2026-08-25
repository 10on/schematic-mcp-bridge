import re

from schematic.layout import auto_layout
from schematic.model import Component, Pin, Schematic
from schematic.renderer import render_svg


def make_schematic() -> Schematic:
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="U1",
            library_id="Device:R",
            value="4.7k",
            label="R1",
            pins=[Pin(number="1", name="A"), Pin(number="2", name="B")],
        )
    )
    schematic.add_component(
        Component(
            id="U2",
            library_id="Device:R",
            value="1k",
            label="R2",
            pins=[Pin(number="1", name="A"), Pin(number="2", name="B")],
        )
    )
    schematic.connect_net("VCC", ["U1.A", "U2.A"])
    return schematic


def test_svg_is_well_formed_root():
    schematic = make_schematic()
    svg = render_svg(schematic, auto_layout(schematic))
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert svg.count("<svg") == svg.count("</svg>")


def test_svg_contains_component_labels_and_values():
    schematic = make_schematic()
    svg = render_svg(schematic, auto_layout(schematic))
    assert "R1" in svg
    assert "R2" in svg
    assert "4.7k" in svg
    assert "1k" in svg


def test_svg_contains_pin_names():
    schematic = make_schematic()
    svg = render_svg(schematic, auto_layout(schematic))
    assert ">A<" in svg
    assert ">B<" in svg


def test_facing_two_endpoint_net_between_neighbors_becomes_a_wire_not_a_label():
    # U1.A/U2.A face each other (layout.py biases side toward the neighbor
    # for a 2-endpoint net) so routing.py connects them directly — no label.
    schematic = make_schematic()
    svg = render_svg(schematic, auto_layout(schematic))
    assert ">VCC<" not in svg
    assert "<polyline" in svg


def test_non_adjacent_two_endpoint_net_is_channel_routed_not_labeled():
    schematic = Schematic(name="demo")
    for component_id in ("U1", "U2", "U3"):
        schematic.add_component(
            Component(
                id=component_id,
                library_id="Device:R",
                pins=[Pin(number="1", name="A"), Pin(number="2", name="B")],
            )
        )
    schematic.connect_net("SIG", ["U1.A", "U3.A"])  # U2 sits physically between them
    svg = render_svg(schematic, auto_layout(schematic))
    assert ">SIG<" not in svg
    assert "<polyline" in svg


def test_bus_net_with_three_endpoints_still_gets_labels():
    schematic = Schematic(name="demo")
    for component_id in ("U1", "U2", "U3"):
        schematic.add_component(
            Component(
                id=component_id,
                library_id="Device:R",
                pins=[Pin(number="1", name="A"), Pin(number="2", name="B")],
            )
        )
    schematic.connect_net("BUS", ["U1.A", "U2.A", "U3.A"])
    svg = render_svg(schematic, auto_layout(schematic))
    assert svg.count(">BUS<") == 3
    assert "<polyline" not in svg


def test_svg_has_one_rect_per_component_plus_background():
    schematic = make_schematic()
    svg = render_svg(schematic, auto_layout(schematic))
    assert len(re.findall(r"<rect", svg)) == 3  # background + 2 components


def test_svg_escapes_special_characters():
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="U1",
            library_id="Custom:Weird",
            label="A&B<C>",
            pins=[Pin(number="1", name="X")],
        )
    )
    svg = render_svg(schematic, auto_layout(schematic))
    assert "A&amp;B&lt;C&gt;" in svg
    assert "A&B<C>" not in svg
