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

Next: Stage 3 — CLI and SVG renderer.

## Development

```bash
python3 -m pip install --user --break-system-packages -e ".[dev]"
PYTHONPATH=. python3 -m pytest
```
