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


def test_svg_contains_pin_names_and_net_label():
    schematic = make_schematic()
    svg = render_svg(schematic, auto_layout(schematic))
    assert ">A<" in svg
    assert ">B<" in svg
    assert ">VCC<" in svg


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
