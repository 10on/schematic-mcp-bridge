"""CLI for the schematic model — search parts, validate, render SVG.

See requirements section 20. `export-kicad` isn't implemented yet
(stage 6).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schematic.layout import auto_layout
from schematic.library import ComponentLibrary
from schematic.model import Schematic
from schematic.renderer import render_svg
from schematic.validation import run_erc

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LIB_DIRS = [REPO_ROOT / "tests" / "fixtures" / "kicad-symbols"]


def cmd_search(args: argparse.Namespace) -> int:
    library = ComponentLibrary(search_paths=args.lib_dir or DEFAULT_LIB_DIRS)
    results = library.search_components(args.query)
    if not results:
        print(f"no components matching '{args.query}'")
        return 1
    for result in results:
        print(f"{result.library_id}  ({result.description})")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    schematic = Schematic.load(args.project)
    report = run_erc(schematic)
    for warning in report["warnings"]:
        print(f"warning: {warning}")
    for error in report["errors"]:
        print(f"error: {error}")
    print(f"{len(report['errors'])} errors, {len(report['warnings'])} warnings")
    return 1 if report["errors"] else 0


def cmd_render(args: argparse.Namespace) -> int:
    schematic = Schematic.load(args.project)
    layout = auto_layout(schematic)
    svg = render_svg(schematic, layout)
    Path(args.output).write_text(svg)
    print(f"wrote {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="schematic")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="search components in KiCad libraries")
    search_parser.add_argument("query")
    search_parser.add_argument("--lib-dir", action="append", help="directory of .kicad_sym files")
    search_parser.set_defaults(func=cmd_search)

    validate_parser = subparsers.add_parser("validate", help="run validation + ERC on a schematic")
    validate_parser.add_argument("project", help="path to schematic JSON")
    validate_parser.set_defaults(func=cmd_validate)

    render_parser = subparsers.add_parser("render", help="render a schematic to SVG")
    render_parser.add_argument("project", help="path to schematic JSON")
    render_parser.add_argument("-o", "--output", required=True, help="output SVG path")
    render_parser.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
