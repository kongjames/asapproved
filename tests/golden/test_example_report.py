"""The shipped example must reproduce its expected report byte for byte (fixed run date)."""

from pathlib import Path

from pharma_agents.assurance.agent import run_check_table
from pharma_agents.assurance.render import to_markdown

EX = Path(__file__).resolve().parents[2] / "examples" / "pharma_tlf"


def test_example_report_is_reproducible():
    report = run_check_table(EX / "recipe.yaml", EX / "approved_sas_table.csv", EX / "candidate_r_table.csv",
                             reviewer="Example Reviewer, Statistical Programmer (personal capacity)",
                             run_date="2026-11-07")
    assert report.verdict == "FAIL"
    c1, c2, c3 = report.checks
    assert c1.passed, "approved table must reproduce from source"
    assert (c2.mismatches, c2.missing, c2.unexpected) == (1, 1, 0)
    assert (c3.mismatches, c3.missing, c3.unexpected) == (1, 1, 0)
    assert to_markdown(report) == (EX / "expected_report.md").read_text()


def test_identical_candidate_passes():
    report = run_check_table(EX / "recipe.yaml", EX / "approved_sas_table.csv", EX / "approved_sas_table.csv",
                             run_date="2026-11-07")
    assert report.verdict == "PASS"
