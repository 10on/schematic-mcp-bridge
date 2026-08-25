"""Builds the ESP32 + INA226 demo from requirements section 22.

Pin data here is hand-authored (Stage 2 will replace this with real
KiCad symbol library lookups via schematic/library.py). Run:

    PYTHONPATH=.. python3 build_esp32_ina226.py
"""

from schematic.model import Component, Pin, Schematic
from schematic.validation import run_erc


def build() -> Schematic:
    schematic = Schematic(name="esp32_ina226")

    schematic.add_component(
        Component(
            id="U1",
            library_id="MCU_Espressif:ESP32-WROOM-32",
            value="ESP32-WROOM-32",
            label="ESP32",
            pins=[
                Pin(number="1", name="3V3", electrical_type="power_in"),
                Pin(number="21", name="GPIO21"),
                Pin(number="22", name="GPIO22"),
                Pin(number="38", name="GND", electrical_type="power_in"),
            ],
        )
    )

    schematic.add_component(
        Component(
            id="U2",
            library_id="Sensor_Current:INA226",
            value="INA226",
            label="INA226",
            pins=[
                Pin(number="1", name="SDA"),
                Pin(number="2", name="SCL"),
                Pin(number="3", name="VS", electrical_type="power_in"),
                Pin(number="4", name="GND", electrical_type="power_in"),
            ],
        )
    )

    for ref in ("R1", "R2"):
        schematic.add_component(
            Component(
                id=ref,
                library_id="Device:R",
                value="4.7k",
                pins=[Pin(number="1", name="1"), Pin(number="2", name="2")],
            )
        )

    schematic.add_component(
        Component(
            id="C1",
            library_id="Device:C",
            value="0.1uF",
            pins=[Pin(number="1", name="1"), Pin(number="2", name="2")],
        )
    )

    schematic.add_component(
        Component(
            id="J1",
            library_id="Connector_Generic:Conn_01x02",
            label="POWER",
            pins=[
                Pin(number="1", name="VCC", electrical_type="power_out"),
                Pin(number="2", name="GND", electrical_type="power_out"),
            ],
        )
    )

    schematic.connect_net(
        "+3V3", ["U1.3V3", "U2.VS", "R1.1", "R2.1", "C1.1", "J1.VCC"]
    )
    schematic.connect_net("GND", ["U1.GND", "U2.GND", "C1.2", "J1.GND"])
    schematic.connect_net("SDA", ["U1.GPIO21", "U2.SDA", "R1.2"])
    schematic.connect_net("SCL", ["U1.GPIO22", "U2.SCL", "R2.2"])

    return schematic


if __name__ == "__main__":
    schematic = build()
    schematic.save("esp32_ina226.json")
    print(f"wrote esp32_ina226.json: {len(schematic.components)} components, {len(schematic.nets)} nets")

    erc = run_erc(schematic)
    print(f"ERC: {len(erc['errors'])} errors, {len(erc['warnings'])} warnings")
    for warning in erc["warnings"]:
        print(f"  warning: {warning}")
    for error in erc["errors"]:
        print(f"  error: {error}")
