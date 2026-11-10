"""E2 — fault injection for ``check-table``.

Start from a candidate table that is identical to the approved one, apply one random mutation,
run the full check (CSV round trip included), and record whether the verdict was what the mutation
demands. A mutation that must be caught and is not is a miss; a mutation that must pass and fails
is a false alarm. Both should be zero by construction; this script measures rather than assumes.

    python evals/fault_injection.py --n 1000 --seed 7 --out evals/RESULTS.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd

from pharma_agents import __version__
from pharma_agents.assurance.agent import run_check_table
from pharma_agents.schema.artifact import Recipe

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "pharma_tlf"

# name -> (must_fail, description)
MUTATIONS = {
    "identity": (False, "no change"),
    "reorder_rows": (False, "rows shuffled; keys and values unchanged"),
    "value_within_tol": (False, "one value moved by less than the recipe tolerance"),
    "key_whitespace": (False, "trailing space added to one key field (keys are trimmed on read)"),
    "value_beyond_tol": (True, "one value moved by more than the recipe tolerance"),
    "swap_values": (True, "two cells with different values exchanged"),
    "drop_cell": (True, "one cell removed"),
    "add_cell": (True, "one cell added under a category that does not exist"),
    "rename_group": (True, "one column label changed on every cell that carries it"),
    "blank_value": (True, "one value blanked"),
}


def mutate(table: pd.DataFrame, kind: str, rng: random.Random, tol_abs: float) -> pd.DataFrame:
    t = table.copy().reset_index(drop=True)
    valued = t.index[t["value"].notna()].tolist()
    if kind == "identity":
        return t
    if kind == "reorder_rows":
        return t.sample(frac=1.0, random_state=rng.randrange(10**9)).reset_index(drop=True)
    if kind == "value_within_tol":
        i = rng.choice(valued)
        t.at[i, "value"] = t.at[i, "value"] + rng.choice([-1, 1]) * rng.uniform(0, tol_abs * 0.8)
        return t
    if kind == "key_whitespace":
        i = rng.randrange(len(t))
        col = rng.choice(["variable", "statistic", "group"])
        t.at[i, col] = str(t.at[i, col]) + " "
        return t
    if kind == "value_beyond_tol":
        i = rng.choice(valued)
        t.at[i, "value"] = t.at[i, "value"] + rng.choice([-1, 1]) * rng.uniform(tol_abs * 2, 10)
        return t
    if kind == "swap_values":
        while True:
            i, j = rng.sample(valued, 2)
            if t.at[i, "value"] != t.at[j, "value"]:
                break
        t.at[i, "value"], t.at[j, "value"] = t.at[j, "value"], t.at[i, "value"]
        return t
    if kind == "drop_cell":
        return t.drop(index=rng.randrange(len(t))).reset_index(drop=True)
    if kind == "add_cell":
        row = t.iloc[rng.randrange(len(t))].copy()
        row["category"] = "ZZZ_NOT_A_CATEGORY"
        return pd.concat([t, row.to_frame().T], ignore_index=True)
    if kind == "rename_group":
        g = rng.choice(sorted(t["group"].unique()))
        t.loc[t["group"] == g, "group"] = g + "_X"
        return t
    if kind == "blank_value":
        i = rng.choice(valued)
        t.at[i, "value"] = None
        return t
    raise ValueError(kind)


def run(n: int, seed: int) -> tuple[Counter, Counter, list[dict]]:
    rng = random.Random(seed)
    recipe = Recipe.load(EXAMPLE / "recipe.yaml")
    approved = pd.read_csv(EXAMPLE / "approved_sas_table.csv")
    kinds = list(MUTATIONS)
    totals, wrong = Counter(), Counter()
    misses: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(n):
            kind = kinds[k % len(kinds)]
            must_fail, _ = MUTATIONS[kind]
            cand = mutate(approved, kind, rng, recipe.tolerances.numeric_abs)
            path = Path(tmp) / f"cand_{k}.csv"
            cand.to_csv(path, index=False)
            report = run_check_table(EXAMPLE / "recipe.yaml", EXAMPLE / "approved_sas_table.csv", path, run_date="eval")
            failed = report.verdict == "FAIL"
            totals[kind] += 1
            if failed != must_fail:
                wrong[kind] += 1
                misses.append({"i": k, "kind": kind, "expected": "FAIL" if must_fail else "PASS", "got": report.verdict})
    return totals, wrong, misses


def render(totals: Counter, wrong: Counter, misses: list[dict], n: int, seed: int) -> str:
    L = ["# Fault-injection results — `check-table`", "",
         (f"Run {dt.date.today().isoformat()} · pharma-agents {__version__} · n = {n} · seed = {seed} · "
          f"example `examples/pharma_tlf` (80 cells, tolerance 0.005)"), "",
         "| Mutation | Must | Runs | Wrong verdicts | Rate |", "|---|---|---:|---:|---:|"]
    for kind, (must_fail, desc) in MUTATIONS.items():
        t, w = totals[kind], wrong[kind]
        L.append(f"| `{kind}` — {desc} | {'FAIL' if must_fail else 'PASS'} | {t} | {w} | {100.0 * w / t if t else 0:.1f}% |")
    must = sum(totals[k] for k, (m, _) in MUTATIONS.items() if m)
    missed = sum(wrong[k] for k, (m, _) in MUTATIONS.items() if m)
    benign = sum(totals[k] for k, (m, _) in MUTATIONS.items() if not m)
    false_alarm = sum(wrong[k] for k, (m, _) in MUTATIONS.items() if not m)
    L += ["", f"**Detection rate** (mutations that must fail and did): {must - missed}/{must} = {100.0 * (must - missed) / must:.2f}%",
          "", f"**False-alarm rate** (benign mutations that failed): {false_alarm}/{benign} = {100.0 * false_alarm / benign:.2f}%", ""]
    if misses:
        L += ["Wrong verdicts:", ""] + [f"- run {m['i']}: `{m['kind']}` expected {m['expected']}, got {m['got']}" for m in misses[:50]]
    else:
        L += ["No wrong verdicts."]
    L += ["", ("Each run writes the mutated candidate to CSV and runs the full `check-table` path, so the CSV round trip is included. "
               "`value_within_tol` moves a value by at most 80% of the tolerance; `value_beyond_tol` by at least twice it. "
               "`key_whitespace` passes by design: keys are trimmed when a table is read."), ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    totals, wrong, misses = run(a.n, a.seed)
    text = render(totals, wrong, misses, a.n, a.seed)
    if a.out:
        a.out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
