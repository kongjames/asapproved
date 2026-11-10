"""Public CDISC pilot ADaM data, via the pharmaverse ``pharmaverseadam`` R package (Apache-2.0).

Nothing here touches private or employer data. The example in this repository ships a CSV
export of ADSL with a subset of columns; ``fetch_adsl`` re-creates it from the upstream
``.rda`` file if you have the optional ``pyreadr`` dependency installed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ADSL_URL = "https://raw.githubusercontent.com/pharmaverse/pharmaverseadam/main/data/adsl.rda"
ADSL_COLUMNS = [
    "STUDYID", "USUBJID", "SITEID", "AGE", "AGEGR1", "AGEU", "SEX", "RACE", "ETHNIC",
    "COUNTRY", "ARM", "ACTARM", "TRT01P", "TRT01A", "SAFFL",
]


def sha256_of(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_csv(path: str | Path) -> pd.DataFrame:
    """Read a dataset CSV. Strings stay strings; nothing is coerced silently."""
    return pd.read_csv(path)


def fetch_adsl(dest: str | Path, url: str = ADSL_URL, columns: list[str] | None = None) -> Path:
    """Download pharmaverseadam's ADSL and write it as CSV (requires ``pip install pharma-agents[data]``)."""
    import urllib.request

    try:
        import pyreadr  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise SystemExit("pyreadr is required: pip install 'pharma-agents[data]'") from exc

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".rda")
    urllib.request.urlretrieve(url, tmp)
    _, df = next(iter(pyreadr.read_r(str(tmp)).items()))
    keep = [c for c in (columns or ADSL_COLUMNS) if c in df.columns]
    df[keep].to_csv(dest, index=False)
    tmp.unlink(missing_ok=True)
    return dest
