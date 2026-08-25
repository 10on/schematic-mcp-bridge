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
  / `group_components` store intent on the model already.
- Stage 5 done: `auto_layout` now honors `left_of`/`right_of` placement
  hints (topological reorder of the row; other relations are still
  ignored, a real 2D layout is stage 7 territory if needed). New
  `schematic/routing.py` draws an actual orthogonal wire between two
  components when they land as immediate neighbors *and* it's a
  2-endpoint net with pins facing each other — otherwise still a net
  label, since routing around an intervening box is real
  routing-algorithm work (deferred). `set_pin_side`/`group_components`
  are still stored-but-unconsumed.
- Stage 6 done: `.kicad_sch` export (`schematic/exporters/kicad.py`),
  reusing SKiDL's own schematic generator rather than hand-rolling a
  KiCad file writer — it already draws real classical symbols with
  correct geometry (section 4/19's stated preference). Only works for
  components sourced from a real library symbol via `add_component`;
  raises `KicadExportError` on a hand-authored/invented component or one
  that doesn't resolve, rather than silently producing a broken file.
  `examples/esp32_ina226.json` can't export (its ESP32/INA226 pins are
  hand-authored placeholders, not real symbols) — see
  `examples/build_rc_filter.py` for a small schematic built entirely
  from real library parts that does. Needed vendoring `power.kicad_sym`
  too (SKiDL's schematic generator loads it unconditionally).

  Also fixed a real bug found while building that RC filter example:
  `ComponentLibrary.instantiate()` defaulted `reference` to the bare
  library ref_prefix ('R' for *every* resistor) instead of
  `component_id` — so adding a second resistor without an explicit
  `reference=` produced a false `duplicate_reference` ERC error on a
  perfectly valid schematic.

MVP is now complete end-to-end (search → add → connect → validate/ERC →
SVG / KiCad export) via both the CLI and the MCP server. What's left is
optional polish: stage 7 (ELK-based 2D layout + general wire routing) is
explicitly "only if this isn't good enough" territory in the spec, not
committed to.

## Development

```bash
python3 -m pip install --user --break-system-packages -e ".[dev]"
PYTHONPATH=. python3 -m pytest

# CLI
PYTHONPATH=. python3 -m cli.main search resistor
PYTHONPATH=. python3 -m cli.main validate examples/esp32_ina226.json
PYTHONPATH=. python3 -m cli.main render examples/esp32_ina226.json -o out.svg
PYTHONPATH=. python3 -m cli.main export-kicad examples/rc_filter.json -o out.kicad_sch

# MCP server (stdio)
PYTHONPATH=. python3 -m mcp_server.server
```
