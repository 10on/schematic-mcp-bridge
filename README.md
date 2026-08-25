# schematic-mcp

AI-agent-friendly system for building electrical schematics: an MCP server
exposes a high-level, semantic API (components, pins, nets) so an LLM never
has to touch coordinates, wires, or `.kicad_sch` internals directly.

```text
AI Agent → MCP / high-level API → semantic schematic model → validation/ERC
    → automatic layout → SVG and/or KiCad schematic
```

See `schematic_mcp_requirements.md` for the full spec (not yet committed
here — see chat history) and `SKILL.md` (once added) for agent rules.

## Status

Stage 1 done: minimal semantic model (`Component`, `Pin`, `Net`,
`Schematic`) with JSON save/load, in `schematic/model.py`.

Next: Stage 2 — KiCad symbol library import + SKiDL-backed
`search_component` / `get_component_pins` / `add_component` / `connect` /
`validate`.

## Development

```bash
python3 -m pip install --user --break-system-packages -e ".[dev]"
PYTHONPATH=. python3 -m pytest
```
