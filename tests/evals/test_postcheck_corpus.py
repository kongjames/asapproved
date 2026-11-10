"""E3 in CI: the labelled corpus must show every built-in fault caught, no false alarms, and the
three blind spots passing (so a future change that starts catching them, or stops warning, is noticed)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _module():
    spec = importlib.util.spec_from_file_location("postcheck_corpus", ROOT / "evals" / "postcheck_corpus.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_corpus_verdicts_match_labels():
    pc = _module()
    status, warned, wrong, _summary = pc.run(per_type=5, seed=1)
    assert not wrong, wrong[:5]
    assert status[("undeclared_figure", "supported")] == 5 and warned["undeclared_figure"] == 5
    assert warned["text_contradicts_declared"] == 5
    for kind in ("right_number_wrong_record", "wrong_reading"):
        assert status[(kind, "supported")] == 5  # documented blind spots
