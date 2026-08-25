import pytest

from schematic.model import (
    Component,
    ComponentNotFoundError,
    DuplicateComponentError,
    PinNotFoundError,
    Pin,
    Schematic,
)


def make_esp32() -> Component:
    return Component(
        id="U1",
        library_id="MCU_Espressif:ESP32-WROOM-32",
        label="ESP32",
        pins=[
            Pin(number="21", name="GPIO21"),
            Pin(number="22", name="GPIO22"),
            Pin(number="38", name="GND"),
        ],
    )


def make_ina226() -> Component:
    return Component(
        id="U2",
        library_id="Sensor_Current:INA226",
        label="INA226",
        pins=[
            Pin(number="1", name="SDA"),
            Pin(number="2", name="SCL"),
            Pin(number="3", name="GND"),
        ],
    )


def make_resistor(ref_id: str) -> Component:
    return Component(
        id=ref_id,
        library_id="Device:R",
        value="4.7k",
        pins=[Pin(number="1", name="1"), Pin(number="2", name="2")],
    )


def test_add_and_remove_component():
    schematic = Schematic(name="demo")
    schematic.add_component(make_esp32())
    assert "U1" in schematic.components

    with pytest.raises(DuplicateComponentError):
        schematic.add_component(make_esp32())

    schematic.remove_component("U1")
    assert "U1" not in schematic.components

    with pytest.raises(ComponentNotFoundError):
        schematic.remove_component("U1")


def test_connect_creates_anonymous_net():
    schematic = Schematic(name="demo")
    schematic.add_component(make_esp32())
    schematic.add_component(make_ina226())

    net_name = schematic.connect("U1.GPIO21", "U2.SDA")
    assert net_name in schematic.nets
    assert set(schematic.nets[net_name].nodes) == {"U1.21", "U2.1"}


def test_connect_accepts_pin_number_or_name():
    schematic = Schematic(name="demo")
    schematic.add_component(make_esp32())
    schematic.add_component(make_ina226())

    schematic.connect("U1.21", "U2.SDA")
    net = next(iter(schematic.nets.values()))
    assert set(net.nodes) == {"U1.21", "U2.1"}


def test_connect_merges_existing_nets():
    schematic = Schematic(name="demo")
    schematic.add_component(make_esp32())
    schematic.add_component(make_ina226())
    schematic.add_component(make_resistor("R1"))

    schematic.connect("U1.GPIO21", "U2.SDA")
    schematic.connect("R1.1", "R1.2")  # unrelated net
    merged_name = schematic.connect("U2.SDA", "R1.1")

    assert len(schematic.nets) == 1
    merged = schematic.nets[merged_name]
    assert set(merged.nodes) == {"U1.21", "U2.1", "R1.1", "R1.2"}


def test_connect_net_named():
    schematic = Schematic(name="demo")
    schematic.add_component(make_esp32())
    schematic.add_component(make_ina226())
    schematic.add_component(make_resistor("R1"))

    schematic.connect_net("SDA", ["U1.GPIO21", "U2.SDA", "R1.1"])
    assert set(schematic.nets["SDA"].nodes) == {"U1.21", "U2.1", "R1.1"}


def test_connect_unknown_pin_raises():
    schematic = Schematic(name="demo")
    schematic.add_component(make_esp32())
    with pytest.raises(PinNotFoundError):
        schematic.connect("U1.GPIO99", "U1.GND")

    with pytest.raises(ComponentNotFoundError):
        schematic.connect("U1.GPIO21", "U9.SDA")


def test_disconnect_removes_pin_and_drops_empty_net():
    schematic = Schematic(name="demo")
    schematic.add_component(make_esp32())
    schematic.add_component(make_ina226())

    schematic.connect("U1.GPIO21", "U2.SDA")
    schematic.disconnect("U2.SDA")
    assert len(schematic.nets) == 1  # net still has U1.21

    schematic.disconnect("U1.GPIO21")
    assert len(schematic.nets) == 0


def test_rename_net():
    schematic = Schematic(name="demo")
    schematic.add_component(make_esp32())
    schematic.add_component(make_ina226())

    net_name = schematic.connect("U1.GPIO21", "U2.SDA")
    schematic.rename_net(net_name, "SDA")
    assert "SDA" in schematic.nets
    assert net_name not in schematic.nets or net_name == "SDA"


def test_remove_component_prunes_nets():
    schematic = Schematic(name="demo")
    schematic.add_component(make_esp32())
    schematic.add_component(make_ina226())

    net_name = schematic.connect("U1.GPIO21", "U2.SDA")
    schematic.remove_component("U2")
    # the net survives with only U1's node left dangling
    assert schematic.nets[net_name].nodes == ["U1.21"]

    schematic.remove_component("U1")
    assert len(schematic.nets) == 0


def test_save_and_load_roundtrip(tmp_path):
    schematic = Schematic(name="esp32_ina226")
    schematic.add_component(make_esp32())
    schematic.add_component(make_ina226())
    schematic.add_component(make_resistor("R1"))
    schematic.connect_net("SDA", ["U1.GPIO21", "U2.SDA", "R1.1"])

    path = tmp_path / "schematic.json"
    schematic.save(path)

    loaded = Schematic.load(path)
    assert loaded.name == "esp32_ina226"
    assert set(loaded.components) == {"U1", "U2", "R1"}
    assert set(loaded.nets["SDA"].nodes) == {"U1.21", "U2.1", "R1.1"}

    # loaded schematic must still be usable for further edits
    loaded.connect("U2.GND", "U1.GND")
    assert len(loaded.nets) == 2
