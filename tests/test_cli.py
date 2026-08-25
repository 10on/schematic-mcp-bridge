from pathlib import Path

from cli.main import main

FIXTURES = Path(__file__).parent / "fixtures" / "kicad-symbols"


def test_search_finds_resistor(capsys):
    exit_code = main(["search", "resistor", "--lib-dir", str(FIXTURES)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Device:R" in out


def test_search_no_match_returns_nonzero(capsys):
    exit_code = main(["search", "definitely-not-a-real-part-xyz", "--lib-dir", str(FIXTURES)])
    assert exit_code == 1


def test_validate_clean_schematic(tmp_path, capsys):
    project = tmp_path / "clean.json"
    project.write_text(
        """
        {"name": "demo", "components": [
            {"id": "J1", "library_id": "Custom:Conn",
             "pins": [{"number": "1", "name": "VCC", "electrical_type": "power_out"}]},
            {"id": "U1", "library_id": "Custom:MCU",
             "pins": [{"number": "1", "name": "3V3", "electrical_type": "power_in"}]}
        ], "nets": [{"name": "VCC", "nodes": ["J1.1", "U1.1"]}]}
        """
    )
    exit_code = main(["validate", str(project)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "0 errors" in out


def test_validate_reports_duplicate_reference(tmp_path, capsys):
    project = tmp_path / "bad.json"
    project.write_text(
        """
        {"name": "demo", "components": [
            {"id": "U1", "library_id": "Custom:MCU", "reference": "U1", "pins": []},
            {"id": "U2", "library_id": "Custom:MCU", "reference": "U1", "pins": []}
        ], "nets": []}
        """
    )
    exit_code = main(["validate", str(project)])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "duplicate_reference" in out


def test_render_writes_svg_file(tmp_path, capsys):
    project = tmp_path / "demo.json"
    project.write_text(
        """
        {"name": "demo", "components": [
            {"id": "U1", "library_id": "Device:R", "value": "1k",
             "pins": [{"number": "1", "name": "1"}, {"number": "2", "name": "2"}]}
        ], "nets": []}
        """
    )
    out_svg = tmp_path / "demo.svg"
    exit_code = main(["render", str(project), "-o", str(out_svg)])
    assert exit_code == 0
    content = out_svg.read_text()
    assert content.startswith("<svg")
    assert "1k" in content
