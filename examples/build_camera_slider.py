"""Real-world test: the camera-slider-esp32 controller board.

Ground truth taken from that project's docs/01_hardware.md, slider.ino
pin #defines, and its own hand-rolled hardware/gen_schematic.py (which
independently reinvented almost exactly this tool's block-mode
approach — custom boxes with labeled pins, no drawn wires). R1/R2 are
real Device:R library parts; everything else (ESP32-C3-Zero dev board,
TMC2209 module, PCF8574/OLED/ADXL345 breakouts, connectors) is
hand-authored, since hobbyist breakout modules like these don't have
real KiCad symbols to search for — same situation as ESP32-WROOM-32 in
esp32_ina226.json.

Run: PYTHONPATH=.. python3 build_camera_slider.py
"""

from schematic.library import ComponentLibrary
from schematic.model import Component, Pin, Schematic
from schematic.validation import run_erc

FIXTURES = "../tests/fixtures/kicad-symbols"


def build() -> Schematic:
    library = ComponentLibrary(search_paths=[FIXTURES])
    schematic = Schematic(name="camera_slider_controller")

    schematic.add_component(
        Component(
            id="J1",
            library_id="Connector:J_BATT",
            label="BATT",
            value="3S-LiPo",
            pins=[
                Pin("1", "VBAT+", electrical_type="power_out"),
                Pin("2", "GND", electrical_type="power_out"),
            ],
        )
    )
    schematic.add_component(
        Component(
            id="U1",
            library_id="Module:DCDC",
            label="DCDC",
            value="MP1584-3V3",
            pins=[
                Pin("1", "IN+", electrical_type="power_in"),
                Pin("2", "GND_IN", electrical_type="power_in"),
                Pin("3", "OUT_3V3", electrical_type="power_out"),
                Pin("4", "GND_OUT", electrical_type="power_out"),
            ],
        )
    )
    schematic.add_component(library.instantiate("Device:R", "R1", value="40.2k"))
    schematic.add_component(library.instantiate("Device:R", "R2", value="10k"))
    schematic.add_component(
        Component(
            id="U2",
            library_id="Module:ESP32-C3-Zero",
            label="ESP32-C3",
            value="ESP32-C3-Zero",
            pins=[
                Pin("1", "GPIO0/EN"), Pin("2", "GPIO1/STEP"), Pin("3", "GPIO2/DIR"),
                Pin("4", "GPIO3/VBAT_ADC"), Pin("5", "GPIO4/TX"), Pin("6", "GPIO5/RX"),
                Pin("7", "3V3", electrical_type="power_in"),
                Pin("8", "GND", electrical_type="power_in"),
                Pin("9", "GPIO8/SDA"), Pin("10", "GPIO9/SCL"),
            ],
        )
    )
    schematic.add_component(
        Component(
            id="U3",
            library_id="Module:TMC2209",
            label="TMC2209",
            value="TMC2209-module",
            pins=[
                Pin("1", "VM", electrical_type="power_in"),
                Pin("2", "GND", electrical_type="power_in"),
                Pin("3", "VIO", electrical_type="power_in"),
                Pin("4", "EN"), Pin("5", "DIR"), Pin("6", "STEP"),
                Pin("7", "UART_RX"), Pin("8", "UART_TX"),
                Pin("9", "A1"), Pin("10", "A2"), Pin("11", "B1"), Pin("12", "B2"),
            ],
        )
    )
    schematic.add_component(
        Component(
            id="U4",
            library_id="Module:PCF8574",
            label="PCF8574",
            value="PCF8574",
            pins=[
                Pin("1", "VCC", electrical_type="power_in"),
                Pin("2", "GND", electrical_type="power_in"),
                Pin("3", "SDA"), Pin("4", "SCL"),
                Pin("5", "P0-nc"), Pin("6", "P1/LED1"), Pin("7", "P2/ENC_CLK"),
                Pin("8", "P3/ENC_DT"), Pin("9", "P4/ENC_SW"),
                Pin("10", "P5/ES1"), Pin("11", "P6/ES2"), Pin("12", "P7/LED2"),
            ],
        )
    )
    schematic.add_component(
        Component(
            id="U5",
            library_id="Module:SSD1306",
            label="OLED",
            value="SSD1306-128x64",
            pins=[
                Pin("1", "VCC", electrical_type="power_in"),
                Pin("2", "GND", electrical_type="power_in"),
                Pin("3", "SCL"), Pin("4", "SDA"),
            ],
        )
    )
    schematic.add_component(
        Component(
            id="U6",
            library_id="Module:ADXL345",
            label="ADXL345",
            value="ADXL345",
            pins=[
                Pin("1", "VCC", electrical_type="power_in"),
                Pin("2", "GND", electrical_type="power_in"),
                Pin("3", "SDA"), Pin("4", "SCL"), Pin("5", "SDO/GND"),
            ],
        )
    )
    schematic.add_component(
        Component(
            id="ENC1",
            library_id="Connector:J_ENCODER",
            label="ENC1",
            value="EC11",
            pins=[Pin("1", "CLK"), Pin("2", "DT"), Pin("3", "SW"), Pin("4", "GND")],
        )
    )
    schematic.add_component(
        Component(
            id="J2",
            library_id="Connector:J_ENDSTOP",
            label="ES1",
            value="Endstop-1",
            pins=[Pin("1", "3V3"), Pin("2", "GND"), Pin("3", "SIG")],
        )
    )
    schematic.add_component(
        Component(
            id="J3",
            library_id="Connector:J_ENDSTOP",
            label="ES2",
            value="Endstop-2",
            pins=[Pin("1", "3V3"), Pin("2", "GND"), Pin("3", "SIG")],
        )
    )
    schematic.add_component(
        Component(
            id="J4",
            library_id="Connector:J_MOTOR",
            label="MOTOR",
            value="Stepper-Motor",
            pins=[Pin("1", "A1"), Pin("2", "A2"), Pin("3", "B1"), Pin("4", "B2")],
        )
    )

    schematic.connect_net("VBAT+", ["J1.1", "U1.1", "R1.1", "U3.1"])
    schematic.connect_net(
        "GND",
        [
            "J1.2", "U1.2", "U1.4", "R2.2", "U2.8", "U3.2", "U4.2", "U5.2",
            "U6.2", "U6.5", "ENC1.4", "J2.2", "J3.2",
        ],
    )
    schematic.connect_net(
        "+3V3", ["U1.3", "U2.7", "U3.3", "U4.1", "U5.1", "U6.1", "J2.1", "J3.1"]
    )
    schematic.connect_net("VBAT_ADC", ["R1.2", "R2.1", "U2.4"])

    schematic.connect_net("TMC_EN", ["U2.1", "U3.4"])
    schematic.connect_net("TMC_STEP", ["U2.2", "U3.6"])
    schematic.connect_net("TMC_DIR", ["U2.3", "U3.5"])
    schematic.connect_net("TMC_TX", ["U2.5", "U3.8"])
    schematic.connect_net("TMC_RX", ["U2.6", "U3.7"])

    schematic.connect_net("SDA", ["U2.9", "U4.3", "U5.4", "U6.3"])
    schematic.connect_net("SCL", ["U2.10", "U4.4", "U5.3", "U6.4"])

    schematic.connect_net("MOT_A1", ["U3.9", "J4.1"])
    schematic.connect_net("MOT_A2", ["U3.10", "J4.2"])
    schematic.connect_net("MOT_B1", ["U3.11", "J4.3"])
    schematic.connect_net("MOT_B2", ["U3.12", "J4.4"])

    schematic.connect_net("PCF_ENC_CLK", ["U4.7", "ENC1.1"])
    schematic.connect_net("PCF_ENC_DT", ["U4.8", "ENC1.2"])
    schematic.connect_net("PCF_ENC_SW", ["U4.9", "ENC1.3"])
    schematic.connect_net("PCF_ES1", ["U4.10", "J2.3"])
    schematic.connect_net("PCF_ES2", ["U4.11", "J3.3"])

    # documents pin intent even though nothing else on this schematic ties to
    # them (matches the original hand-rolled gen_schematic.py exactly)
    schematic.connect_net("NC", ["U4.5"])
    schematic.connect_net("PCF_LED1", ["U4.6"])
    schematic.connect_net("PCF_LED2", ["U4.12"])

    return schematic


if __name__ == "__main__":
    schematic = build()
    schematic.save("camera_slider.json")
    print(
        f"wrote camera_slider.json: {len(schematic.components)} components, "
        f"{len(schematic.nets)} nets"
    )

    erc = run_erc(schematic)
    print(f"ERC: {len(erc['errors'])} errors, {len(erc['warnings'])} warnings")
    for warning in erc["warnings"]:
        print(f"  warning: {warning}")
    for error in erc["errors"]:
        print(f"  error: {error}")
