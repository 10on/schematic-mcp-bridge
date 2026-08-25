from pathlib import Path

import pytest

from schematic.exporters.kicad import KicadExportError, export_kicad
from schematic.library import ComponentLibrary
from schematic.model import Component, Pin, Schematic

FIXTURES = Path(__file__).parent / "fixtures" / "kicad-symbols"


def make_real_schematic() -> Schematic:
    lib = ComponentLibrary(search_paths=[FIXTURES])
    schematic = Schematic(name="demo")
    schematic.add_component(lib.instantiate("Device:R", "R1", value="4.7k"))
    schematic.add_component(lib.instantiate("Device:C", "C1", value="0.1uF"))
    schematic.connect("R1.1", "C1.1")
    return schematic


def test_export_writes_valid_kicad_sch(tmp_path):
    out_path = tmp_path / "demo.kicad_sch"
    result = export_kicad(make_real_schematic(), out_path, lib_search_paths=[FIXTURES])

    assert result == out_path
    assert out_path.exists()
    content = out_path.read_text()
    assert content.startswith("(kicad_sch")
    assert '"R1"' in content
    assert '"C1"' in content
    assert "Device:R" in content
    assert "Device:C" in content


def test_export_rejects_component_without_real_library_id(tmp_path):
    schematic = Schematic(name="demo")
    schematic.add_component(
        Component(id="X1", library_id="hand-authored", pins=[Pin(number="1", name="1")])
    )
    with pytest.raises(KicadExportError):
        export_kicad(schematic, tmp_path / "out.kicad_sch", lib_search_paths=[FIXTURES])


def test_export_rejects_unresolvable_library_symbol(tmp_path):
    schematic = Schematic(name="demo")
    schematic.add_component(Component(id="X1", library_id="Device:NoSuchPart", pins=[]))
    with pytest.raises(KicadExportError):
        export_kicad(schematic, tmp_path / "out.kicad_sch", lib_search_paths=[FIXTURES])
