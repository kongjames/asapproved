"""The README images are generated; the checked-in SVGs must match what the generator produces."""

import importlib.util
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[2] / "assets"


def _generator():
    spec = importlib.util.spec_from_file_location("make_assets", ASSETS / "make_assets.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_checked_in_svgs_match_generator():
    mod = _generator()
    rendered = mod.render_all()
    assert set(rendered) == {p.name for p in ASSETS.glob("*.svg")}
    for name, content in rendered.items():
        assert (ASSETS / name).read_text(encoding="utf-8") == content, f"regenerate: {name}"


def test_svgs_are_well_formed_and_carry_titles():
    import xml.dom.minidom

    for p in ASSETS.glob("*.svg"):
        doc = xml.dom.minidom.parse(str(p))
        assert doc.getElementsByTagName("title")[0].firstChild.data.strip()
