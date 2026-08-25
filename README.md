# schematic-mcp

AI-agent-friendly system for building electrical schematics: an MCP server
exposes a high-level, semantic API (components, pins, nets) so an LLM never
has to touch coordinates, wires, or `.kicad_sch` internals directly.

```text
AI Agent → MCP / high-level API → semantic schematic model → validation/ERC
    → automatic layout → SVG and/or KiCad schematic
```

See `schematic_mcp_requirements.md` for the full spec and `SKILL.md`
(once added) for agent rules.

## Status

- Stage 1 done: minimal semantic model (`Component`, `Pin`, `Net`,
  `Schematic`) with JSON save/load, in `schematic/model.py`.
- Stage 2 done: KiCad symbol library import backed by SKiDL
  (`schematic/library.py`: `search_components` / `get_component_pins` /
  `instantiate`) and structural validation + basic ERC
  (`schematic/validation.py`: `validate` / `run_erc`). Tested against real
  official KiCad symbol libraries vendored in `tests/fixtures/kicad-symbols/`
  (`Device`, `MCU_Espressif`, `Sensor_Current`).
- Stage 3 done: naive auto layout (`schematic/layout.py`, one row of
  boxes, no overlap), an SVG renderer (`schematic/renderer.py`) that
  draws component boxes with pin numbers/names and net-name labels next
  to each pin — no drawn wires yet, connectivity is shown via labels
  (see requirements section 11); and a CLI (`cli/main.py`: `search`,
  `validate`, `render`).
- Stage 4 done: MCP server (`mcp_server/server.py`) exposing the full
  section 8 tool list — library lookup, schematic lifecycle,
  connections, layout hints, validation/ERC, SVG output — over stdio.
  The stateful logic lives in `mcp_server/tools.py::SchematicSession`
  (one active schematic per session), framework-free so it's tested
  directly without an MCP client. `set_placement_hint` / `set_pin_side`
  / `group_components` store intent on the model already — `auto_layout`
  doesn't consume it yet, that's stage 5. `export_kicad` raises
  `NotImplementedError` (stage 6).

Next: Stage 5 — real placement heuristics + wire routing.

## Development

```bash
python3 -m pip install --user --break-system-packages -e ".[dev]"
PYTHONPATH=. python3 -m pytest

# CLI
PYTHONPATH=. python3 -m cli.main search resistor
PYTHONPATH=. python3 -m cli.main validate examples/esp32_ina226.json
PYTHONPATH=. python3 -m cli.main render examples/esp32_ina226.json -o out.svg

# MCP server (stdio)
PYTHONPATH=. python3 -m mcp_server.server
```
