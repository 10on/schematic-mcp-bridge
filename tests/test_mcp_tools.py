from pathlib import Path

import pytest

from mcp_server.tools import NoActiveSchematicError, SchematicSession
from schematic.model import ComponentNotFoundError

FIXTURES = Path(__file__).parent / "fixtures" / "kicad-symbols"


@pytest.fixture
def session():
    return SchematicSession(lib_search_paths=[FIXTURES])


def test_search_and_get_component(session):
    results = session.search_components("resistor")
    assert any(r["library_id"] == "Device:R" for r in results)

    component = session.get_component("Device:R")
    assert component["ref_prefix"] == "R"
    assert len(component["pins"]) == 2


def test_operations_require_active_schematic(session):
    with pytest.raises(NoActiveSchematicError):
        session.add_component("Device:R", "R1")


def test_full_workflow(session):
    session.create_schematic("demo")

    session.add_component("Device:R", "R1", value="4.7k")
    session.add_component("Device:C", "C1", value="0.1uF")

    net = session.connect("R1.1", "C1.1")
    assert net["net"]

    validation = session.validate()
    assert validation["errors"] == []

    erc = session.run_erc()
    assert erc["errors"] == []

    layout = session.auto_layout()
    assert layout["components"] == 2

    preview = session.get_preview()
    assert preview["svg"].startswith("<svg")


def test_remove_unknown_component_raises(session):
    session.create_schematic("demo")
    with pytest.raises(ComponentNotFoundError):
        session.remove_component("nope")


def test_set_placement_hint_and_pin_side(session):
    session.create_schematic("demo")
    session.add_component("Device:R", "R1")

    hinted = session.set_placement_hint("R1", "left_of", "R2")
    assert hinted["placement_hint"] == {"relation": "left_of", "target": "R2"}

    pin = session.set_pin_side("R1", "1", "top")
    assert pin["side"] == "top"


def test_group_components(session):
    session.create_schematic("demo")
    session.add_component("Device:R", "R1")
    session.add_component("Device:R", "R2")

    result = session.group_components("pullups", ["R1", "R2"])
    assert result["group"] == "pullups"


def test_save_and_load_roundtrip(session, tmp_path):
    session.create_schematic("demo")
    session.add_component("Device:R", "R1", value="4.7k")
    path = tmp_path / "demo.json"
    session.save_schematic(str(path))

    other = SchematicSession(lib_search_paths=[FIXTURES])
    info = other.load_schematic(str(path))
    assert info["components"] == 1


def test_export_kicad_writes_file(session, tmp_path):
    session.create_schematic("demo")
    session.add_component("Device:R", "R1", value="4.7k")
    session.add_component("Device:C", "C1", value="0.1uF")
    session.connect("R1.1", "C1.1")

    out_path = tmp_path / "demo.kicad_sch"
    result = session.export_kicad(str(out_path))

    assert result == {"exported": str(out_path)}
    assert out_path.exists()
    assert out_path.read_text().startswith("(kicad_sch")
