"""E2 in CI: a short, seeded fault-injection run must show no misses and no false alarms."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _module():
    spec = importlib.util.spec_from_file_location("fault_injection", ROOT / "evals" / "fault_injection.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_short_fault_injection_run_has_no_wrong_verdicts():
    fi = _module()
    totals, _wrong, misses = fi.run(n=120, seed=1)
    assert sum(totals.values()) == 120
    assert set(totals) == set(fi.MUTATIONS)
    assert not misses, misses[:5]
