"""E3 — labelled fault corpus for the brief post-check (C1 citation trace, C2 number trace).

Claims are generated from the records captured for ``examples/pharma_brief`` (three ClinicalTrials.gov
studies, one openFDA label, one FAERS count record). Each claim carries a labelled fault, or no
fault, and the corpus measures what the post-check catches and, just as important, what it cannot
catch by design.

    python evals/postcheck_corpus.py --per-type 10 --seed 3 --out evals/RESULTS_POSTCHECK.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
from collections import Counter
from pathlib import Path

from pharma_agents import __version__
from pharma_agents.research.postcheck import check_brief, resolve_path
from pharma_agents.schema.brief import Claim, EvidenceBrief, NumberRef
from pharma_agents.sources.base import RecordStore

RECORDS = Path(__file__).resolve().parents[1] / "examples" / "pharma_brief" / "records"

# kind -> (expected status, description)
MUST_FAIL = "unsupported"
MUST_PASS = "supported"
BLIND = "supported (by design: the check cannot see this)"
KINDS = {
    "correct": (MUST_PASS, "number matches the value at its path in the cited record"),
    "correct_numeric_string": (MUST_PASS, "value at the path is a numeric string (label version); coerced and compared"),
    "undeclared_figure": (MUST_PASS, "a second figure in the text has no numbers entry (warning, not failure)"),
    "wrong_number": (MUST_FAIL, "declared value differs from the value at the path"),
    "ghost_record": (MUST_FAIL, "record_ids cites an id that is not in the store"),
    "number_in_ghost_record": (MUST_FAIL, "a number cites a record that is not in the store"),
    "wrong_path": (MUST_FAIL, "the path does not exist in the record"),
    "non_numeric_path": (MUST_FAIL, "the path exists but holds text"),
    "no_citation": (MUST_FAIL, "the claim cites no record at all"),
    "right_number_wrong_record": (BLIND, "text is about study A; the number is real but taken from study B and cited to B"),
    "wrong_reading": (BLIND, "the number is real and traced, but the text says it means something it does not"),
    "text_contradicts_declared": (BLIND, "the text states a different figure than the declared number (warning only)"),
}


def _numeric_paths(store: dict) -> list[tuple[str, str, float]]:
    out = []
    for rid, rec in store.items():
        if rec.source == "clinicaltrials.gov":
            out.append((rid, "enrollment_count", float(rec.payload["enrollment_count"])))
        elif rec.source == "openfda.event":
            for i, t in enumerate(rec.payload["terms"]):
                out.append((rid, f"terms[{i}].count", float(t["count"])))
    return out


def build_claim(kind: str, i: int, rng: random.Random, store: dict, paths: list) -> Claim:
    rid, path, value = rng.choice(paths)
    cid = f"{kind}-{i}"
    study = store[rid].payload.get("nct_id", rid)
    base_text = f"Record {study} lists {value:g}."  # no path in the text: an index like [0] would read as a figure
    if kind == "correct":
        return Claim(id=cid, text=base_text, record_ids=[rid], numbers=[NumberRef(value=value, record_id=rid, path=path)])
    if kind == "correct_numeric_string":
        lab = next(r for r in store.values() if r.source == "openfda.label")
        v = float(lab.payload["version"])
        return Claim(id=cid, text=f"The label is version {v:g}.", record_ids=[lab.record_id],
                     numbers=[NumberRef(value=v, record_id=lab.record_id, path="version")])
    if kind == "undeclared_figure":
        extra = rng.randrange(100, 999)
        return Claim(id=cid, text=base_text + f" About {extra} sites took part.", record_ids=[rid],
                     numbers=[NumberRef(value=value, record_id=rid, path=path)])
    if kind == "wrong_number":
        wrong = value + rng.choice([-1, 1]) * rng.randrange(1, 50)
        return Claim(id=cid, text=base_text.replace(f"{value:g}", f"{wrong:g}"), record_ids=[rid],
                     numbers=[NumberRef(value=wrong, record_id=rid, path=path)])
    if kind == "ghost_record":
        ghost = f"NCT{rng.randrange(10**7, 10**8)}"
        return Claim(id=cid, text=f"Record {ghost} exists.", record_ids=[ghost], numbers=[])
    if kind == "number_in_ghost_record":
        ghost = f"NCT{rng.randrange(10**7, 10**8)}"
        return Claim(id=cid, text=f"Record {ghost} lists {value:g}.", record_ids=[rid],
                     numbers=[NumberRef(value=value, record_id=ghost, path=path)])
    if kind == "wrong_path":
        return Claim(id=cid, text=base_text, record_ids=[rid],
                     numbers=[NumberRef(value=value, record_id=rid, path=f"no_such_field_{i}")])
    if kind == "non_numeric_path":
        text_path = "brief_title" if store[rid].source == "clinicaltrials.gov" else "generic_name"
        return Claim(id=cid, text=base_text, record_ids=[rid],
                     numbers=[NumberRef(value=value, record_id=rid, path=text_path)])
    if kind == "no_citation":
        return Claim(id=cid, text=base_text, record_ids=[], numbers=[])
    if kind == "right_number_wrong_record":
        others = [p for p in paths if p[0] != rid]
        rid2, path2, value2 = rng.choice(others)
        return Claim(id=cid, text=f"Record {study} enrolled {value2:g} participants.", record_ids=[rid2],
                     numbers=[NumberRef(value=value2, record_id=rid2, path=path2)])
    if kind == "wrong_reading":
        return Claim(id=cid, text=f"Record {study} reports {value:g} deaths.", record_ids=[rid],
                     numbers=[NumberRef(value=value, record_id=rid, path=path)])
    if kind == "text_contradicts_declared":
        stated = value + rng.randrange(1, 50)
        return Claim(id=cid, text=f"Record {study} lists {stated:g}.", record_ids=[rid],
                     numbers=[NumberRef(value=value, record_id=rid, path=path)])
    raise ValueError(kind)


def run(per_type: int, seed: int):
    rng = random.Random(seed)
    store = RecordStore(RECORDS).index()
    store = {k: v for k, v in store.items() if ":" in k or k.startswith("NCT") or len(k) == 36}  # record_id keys only
    # keep one key per record (index() stores both key and record_id); prefer record_id
    by_id = {v.record_id: v for v in store.values()}
    paths = _numeric_paths(by_id)
    for rid, path, value in paths:
        assert float(resolve_path(by_id[rid].payload, path)) == value
    claims = [build_claim(kind, i, rng, by_id, paths) for kind in KINDS for i in range(per_type)]
    brief = EvidenceBrief(question="corpus", summary="Generated corpus; no digits here.", claims=claims)
    checked, summary = check_brief(brief, by_id)
    status = Counter()
    warned = Counter()
    wrong: list[dict] = []
    for c in checked.claims:
        kind = c.id.rsplit("-", 1)[0]
        expected = KINDS[kind][0].split(" ")[0]
        status[(kind, c.status)] += 1
        if c.warnings:
            warned[kind] += 1
        if c.status != expected:
            wrong.append({"id": c.id, "expected": expected, "got": c.status, "reasons": c.reasons})
    return status, warned, wrong, summary


def render(status, warned, wrong, summary, per_type, seed) -> str:
    L = ["# Post-check corpus results — `check-brief`", "",
         (f"Run {dt.date.today().isoformat()} · pharma-agents {__version__} · {per_type} claims per kind · seed = {seed} · "
          f"records from `examples/pharma_brief/records` ({summary.record_ids_cited} distinct ids cited)"), "",
         "| Kind | Expected | Supported | Unsupported | Warned | Description |", "|---|---|---:|---:|---:|---|"]
    for kind, (exp, desc) in KINDS.items():
        s, u = status[(kind, "supported")], status[(kind, "unsupported")]
        L.append(f"| `{kind}` | {exp} | {s} | {u} | {warned[kind]} | {desc} |")
    must_fail = [k for k, (e, _) in KINDS.items() if e == MUST_FAIL]
    must_pass = [k for k, (e, _) in KINDS.items() if e == MUST_PASS]
    blind = [k for k, (e, _) in KINDS.items() if e == BLIND]
    caught = sum(status[(k, "unsupported")] for k in must_fail)
    fa = sum(status[(k, "unsupported")] for k in must_pass)
    blind_passed = sum(status[(k, "supported")] for k in blind)
    L += ["", f"**Catch rate** on faults the check is built to catch: {caught}/{per_type * len(must_fail)}",
          "", f"**False alarms** on correct claims: {fa}/{per_type * len(must_pass)}",
          "", f"**Blind spots** passed as supported, by design: {blind_passed}/{per_type * len(blind)} "
              f"(`text_contradicts_declared` warned on {warned['text_contradicts_declared']}/{per_type})", ""]
    if wrong:
        L += ["Unexpected verdicts:", ""] + [f"- `{w['id']}`: expected {w['expected']}, got {w['got']} {w['reasons']}" for w in wrong[:50]]
    else:
        L += ["No unexpected verdicts."]
    note = ("The three blind-spot kinds are the limit of a deterministic trace: it proves a number was found where "
            "the claim says it was, not that the claim reads it correctly or cites the record it is about. "
            "`text_contradicts_declared` is surfaced as a warning (an undeclared figure in the text), never as a failure. "
            "A reviewer, or a labelled model judgement (planned C3), is needed for these.")
    L += ["", note, ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-type", type=int, default=10)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    text = render(*run(a.per_type, a.seed), a.per_type, a.seed)
    if a.out:
        a.out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
