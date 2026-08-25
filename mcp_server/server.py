"""MCP server exposing the schematic tool API (requirements section 8).

Run with: python3 -m mcp_server.server
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from mcp_server.tools import SchematicSession

mcp = MCPServer(
    name="schematic-mcp",
    instructions=(
        "Build electrical schematics through a semantic API: components, "
        "pins, nets. Never guess pin names — call get_component_pins first. "
        "Always connect() / connect_net() before auto_layout()/render_svg(). "
        "Run validate() and run_erc() after significant edits."
    ),
)

session = SchematicSession()

TOOLS = [
    session.search_components,
    session.get_component,
    session.get_component_pins,
    session.create_schematic,
    session.load_schematic,
    session.save_schematic,
    session.add_component,
    session.remove_component,
    session.set_component_value,
    session.connect,
    session.connect_net,
    session.disconnect,
    session.rename_net,
    session.set_placement_hint,
    session.set_pin_side,
    session.group_components,
    session.auto_layout,
    session.validate,
    session.run_erc,
    session.render_svg,
    session.get_preview,
]

for _tool in TOOLS:
    mcp.tool()(_tool)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
