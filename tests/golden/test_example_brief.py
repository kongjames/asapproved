"""The shipped example brief must check the same way on every machine."""

from pathlib import Path

from typer.testing import CliRunner

from pharmaagents.cli import app

EX = Path(__file__).resolve().parents[2] / "examples" / "pharma_brief"


def test_check_brief_matches_expected_report(tmp_path):
    out = tmp_path / "report.md"
    r = CliRunner().invoke(app, ["check-brief", str(EX / "brief.json"), "--out", str(out),
                                 "--reviewer", "Example Reviewer (personal capacity)", "--date", "2026-11-07"])
    assert r.exit_code == 1, r.output  # two deliberate faults → FAIL
    assert "FAIL c3" in r.output and "FAIL c4" in r.output and "OK   c1" in r.output
    assert out.read_text(encoding="utf-8") == (EX / "expected_report.md").read_text(encoding="utf-8")
