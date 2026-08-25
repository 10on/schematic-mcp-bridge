from pathlib import Path

import pytest

from schematic.library import ComponentLibrary, ComponentNotInLibraryError

FIXTURES = Path(__file__).parent / "fixtures" / "kicad-symbols"


@pytest.fixture
def library():
    return ComponentLibrary(search_paths=[FIXTURES])


def test_search_finds_resistor(library):
    results = library.search_components("resistor")
    library_ids = {r.library_id for r in results}
    assert "Device:R" in library_ids


def test_search_matches_keywords(library):
    results = library.search_components("res")
    assert any(r.library_id == "Device:R" for r in results)


def test_search_unknown_query_returns_empty(library):
    assert library.search_components("definitely-not-a-real-part-xyz") == []


def test_get_component_pins_resistor(library):
    pins = library.get_component_pins("Device:R")
    assert len(pins) == 2
    assert {p.number for p in pins} == {"1", "2"}
    assert all(p.electrical_type == "passive" for p in pins)


def test_get_component_pins_capacitor(library):
    pins = library.get_component_pins("Device:C")
    assert {p.number for p in pins} == {"1", "2"}


def test_unknown_component_raises(library):
    with pytest.raises(ComponentNotInLibraryError):
        library.get_component_pins("Device:NoSuchPart")


def test_instantiate_builds_component(library):
    component = library.instantiate("Device:R", component_id="R1", value="4.7k")
    assert component.id == "R1"
    assert component.library_id == "Device:R"
    assert component.reference == "R1"
    assert component.value == "4.7k"
    assert len(component.pins) == 2


def test_instantiate_reference_defaults_to_component_id_not_bare_prefix(library):
    # Regression test: reference used to default to the library's bare
    # ref_prefix ('R' for every resistor), so a second resistor got the
    # same reference as the first — a false duplicate_reference error on
    # a perfectly valid schematic. It must default to component_id instead.
    r1 = library.instantiate("Device:R", component_id="R1")
    r2 = library.instantiate("Device:R", component_id="R2")
    assert r1.reference == "R1"
    assert r2.reference == "R2"


def test_instantiate_explicit_reference_overrides_default(library):
    component = library.instantiate("Device:R", component_id="R1", reference="R99")
    assert component.reference == "R99"


def test_get_component_ref_prefix_correct_without_prior_parse():
    # Regression test for a bug where ref_prefix read SKiDL's un-parsed
    # placeholder ('U' for every part) instead of the real prefix — only
    # visible on a part no earlier test has touched, since SKiDL caches
    # parsed parts globally and earlier tests would mask it. Device:LED
    # is not used by any other test in this file.
    library = ComponentLibrary(search_paths=[FIXTURES])
    component = library.get_component("Device:LED")
    assert component["ref_prefix"] == "D"


def test_instantiate_esp32s3_has_many_pins(library):
    component = library.instantiate("MCU_Espressif:ESP32-S3", component_id="U1")
    assert len(component.pins) > 10
