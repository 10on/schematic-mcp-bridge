---
name: schematic-mcp
description: Rules for building electrical schematics through the schematic-mcp semantic API (search_components, add_component, connect, validate, run_erc, render_svg, export_kicad).
---

- Always build the electrical netlist before layout: `search_components` →
  `get_component_pins` → `add_component` → `connect`/`connect_net`.
- Never invent component pins. Query real pin numbers/names with
  `get_component_pins` (or `get_component`) before connecting — don't
  guess from a datasheet you remember.
- Prefer semantic pin references (`U1.GPIO21`, `U1.SDA`) over anything
  positional.
- Run `validate()` and `run_erc()` after every significant edit, before
  rendering. Fix errors before continuing; warnings (e.g.
  `unconnected_pin`, `power_input_not_driven`) are worth a second look
  but don't block.
- Signal flow should generally go left to right; the auto layout is a
  single row, so this mostly happens on its own from insertion order.
  Use `set_placement_hint(component_id, "left_of"/"right_of", target)`
  if a specific ordering matters.
- Call `auto_layout()` before `render_svg()`/`get_preview()` if you've
  added or removed components since the last layout — otherwise the
  render uses stale positions.
- Don't manually route wires or pick coordinates — there's no tool for
  that on purpose (see requirements section 9). `render_svg` decides
  real wires vs. net labels on its own.
- If `render_svg`/`export_kicad` fails or looks wrong, treat it as a
  layout/renderer issue, not a reason to change the electrical netlist —
  don't "fix" a rendering problem by rewiring a net that's actually
  correct.
- `export_kicad` only works for components added via `add_component`
  from a real library symbol. A component instantiated with a
  hand-authored `library_id` (no real KiCad symbol behind it) will
  raise `KicadExportError` — that's expected, not a bug to work around.
