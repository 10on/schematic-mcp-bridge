from schematic.layout import auto_layout
from schematic.model import Component, Pin, Schematic


def make_schematic() -> Schematic:
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="U1",
            library_id="Device:R",
            pins=[Pin(number="1", name="1"), Pin(number="2", name="2")],
        )
    )
    schematic.add_component(
        Component(
            id="U2",
            library_id="Device:C",
            pins=[Pin(number="1", name="1"), Pin(number="2", name="2")],
        )
    )
    return schematic


def test_every_component_gets_a_box():
    layout = auto_layout(make_schematic())
    assert set(layout.boxes) == {"U1", "U2"}


def test_boxes_do_not_overlap_horizontally():
    layout = auto_layout(make_schematic())
    u1, u2 = layout.boxes["U1"], layout.boxes["U2"]
    assert u1.x + u1.width < u2.x


def test_every_visible_pin_has_a_position():
    layout = auto_layout(make_schematic())
    box = layout.boxes["U1"]
    assert set(box.pins) == {"1", "2"}
    for pin_pos in box.pins.values():
        assert box.x <= pin_pos.x <= box.x + box.width
        assert box.y <= pin_pos.y <= box.y + box.height


def test_hidden_pins_are_skipped():
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="U1",
            library_id="Device:R",
            pins=[Pin(number="1", name="1"), Pin(number="2", name="2", hidden=True)],
        )
    )
    layout = auto_layout(schematic)
    assert set(layout.boxes["U1"].pins) == {"1"}


def test_layout_bounds_cover_all_boxes():
    layout = auto_layout(make_schematic())
    for box in layout.boxes.values():
        assert box.x + box.width <= layout.width
        assert box.y + box.height <= layout.height


def test_left_of_hint_reorders_placement():
    schematic = Schematic(name="demo")
    schematic.add_component(Component(id="A", library_id="Device:R", pins=[]))
    schematic.add_component(Component(id="B", library_id="Device:R", pins=[]))
    # inserted after B, but hinted to sit to B's left
    schematic.add_component(
        Component(
            id="C", library_id="Device:R", pins=[], placement_hint={"relation": "left_of", "target": "B"}
        )
    )

    layout = auto_layout(schematic)
    assert layout.boxes["C"].x < layout.boxes["B"].x


def test_right_of_hint_reorders_placement():
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="A", library_id="Device:R", pins=[], placement_hint={"relation": "right_of", "target": "B"}
        )
    )
    schematic.add_component(Component(id="B", library_id="Device:R", pins=[]))

    layout = auto_layout(schematic)
    assert layout.boxes["A"].x > layout.boxes["B"].x


def test_hint_referencing_unknown_component_is_ignored():
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="A",
            library_id="Device:R",
            pins=[],
            placement_hint={"relation": "left_of", "target": "does-not-exist"},
        )
    )
    layout = auto_layout(schematic)
    assert "A" in layout.boxes  # doesn't raise, just ignores the bad hint


def test_conflicting_hints_do_not_raise():
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="A", library_id="Device:R", pins=[], placement_hint={"relation": "left_of", "target": "B"}
        )
    )
    schematic.add_component(
        Component(
            id="B", library_id="Device:R", pins=[], placement_hint={"relation": "left_of", "target": "A"}
        )
    )
    layout = auto_layout(schematic)
    assert set(layout.boxes) == {"A", "B"}
