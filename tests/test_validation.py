from schematic.model import Component, Pin, Schematic
from schematic.validation import run_erc, validate


def build_basic_schematic() -> Schematic:
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="U1",
            library_id="Device:R",
            reference="R1",
            pins=[Pin(number="1", name="1"), Pin(number="2", name="2")],
        )
    )
    schematic.add_component(
        Component(
            id="U2",
            library_id="Device:R",
            reference="R2",
            pins=[Pin(number="1", name="1"), Pin(number="2", name="2")],
        )
    )
    return schematic


def test_validate_reports_unconnected_pins():
    schematic = build_basic_schematic()
    result = validate(schematic)
    assert result["errors"] == []
    assert len(result["warnings"]) == 4  # all 4 pins unconnected


def test_validate_no_warnings_when_fully_connected():
    schematic = build_basic_schematic()
    schematic.connect("U1.1", "U2.1")
    schematic.connect("U1.2", "U2.2")
    result = validate(schematic)
    assert result["warnings"] == []


def test_validate_flags_duplicate_reference():
    schematic = build_basic_schematic()
    schematic.components["U2"].reference = "R1"
    result = validate(schematic)
    errors = [e for e in result["errors"] if e["type"] == "duplicate_reference"]
    assert len(errors) == 1
    assert set(errors[0]["components"]) == {"U1", "U2"}


def test_erc_flags_output_conflict():
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="U1",
            library_id="Custom:Driver",
            pins=[Pin(number="1", name="OUT", electrical_type="output")],
        )
    )
    schematic.add_component(
        Component(
            id="U2",
            library_id="Custom:Driver",
            pins=[Pin(number="1", name="OUT", electrical_type="output")],
        )
    )
    schematic.connect("U1.OUT", "U2.OUT")

    result = run_erc(schematic)
    conflicts = [e for e in result["errors"] if e["type"] == "output_conflict"]
    assert len(conflicts) == 1


def test_erc_flags_undriven_power_net():
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="U1",
            library_id="Custom:MCU",
            pins=[Pin(number="1", name="3V3", electrical_type="power_in")],
        )
    )
    schematic.add_component(
        Component(
            id="U2",
            library_id="Custom:MCU",
            pins=[Pin(number="1", name="VDD", electrical_type="power_in")],
        )
    )
    schematic.connect("U1.3V3", "U2.VDD")

    result = run_erc(schematic)
    undriven = [w for w in result["warnings"] if w["type"] == "power_input_not_driven"]
    assert len(undriven) == 1


def test_erc_power_net_driven_by_power_out_has_no_warning():
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(
            id="J1",
            library_id="Custom:Connector",
            pins=[Pin(number="1", name="VCC", electrical_type="power_out")],
        )
    )
    schematic.add_component(
        Component(
            id="U1",
            library_id="Custom:MCU",
            pins=[Pin(number="1", name="3V3", electrical_type="power_in")],
        )
    )
    schematic.connect("J1.VCC", "U1.3V3")

    result = run_erc(schematic)
    undriven = [w for w in result["warnings"] if w["type"] == "power_input_not_driven"]
    assert undriven == []
