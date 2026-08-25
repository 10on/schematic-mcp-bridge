"""A tiny RC low-pass filter, built entirely from real KiCad library
parts (unlike esp32_ina226.json, whose ESP32/INA226 pins are
hand-authored placeholders — see its docstring). This one can actually
go through export_kicad(), since every component resolves to a real
`.kicad_sym` symbol. Run:

    PYTHONPATH=.. python3 build_rc_filter.py
"""

from schematic.library import ComponentLibrary
from schematic.model import Schematic
from schematic.validation import run_erc

FIXTURES = "../tests/fixtures/kicad-symbols"


def build() -> Schematic:
    library = ComponentLibrary(search_paths=[FIXTURES])
    schematic = Schematic(name="rc_filter")

    schematic.add_component(library.instantiate("Device:R", "R1", value="1k"))
    schematic.add_component(library.instantiate("Device:C", "C1", value="0.1uF"))

    schematic.connect("R1.2", "C1.1")

    return schematic


if __name__ == "__main__":
    schematic = build()
    schematic.save("rc_filter.json")
    print(f"wrote rc_filter.json: {len(schematic.components)} components, {len(schematic.nets)} nets")

    erc = run_erc(schematic)
    print(f"ERC: {len(erc['errors'])} errors, {len(erc['warnings'])} warnings")
