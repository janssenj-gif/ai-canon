"""Stage C — static site generation smoke tests (CAN-21..25)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from canon import export_site as site

_REL = Path(__file__).resolve().parents[1] / "data" / "releases" / site.VERSION

pytestmark = pytest.mark.skipif(
    not (_REL / "release.json").exists(), reason="no release — run `make release` first"
)


def test_build_emits_core_pages_and_work_pages():
    summary = site.build()
    for name in ("canon-50.html", "papers.html", "method.html", "challenges.html",
                 "changelog.html", "data.html"):
        assert (site.SITE / name).exists(), name
    assert summary["work_pages"] > 0
    assert summary["home_teaser_injected"] is True


def test_no_broken_internal_links():
    site.build()
    broken = []
    for html in site.SITE.rglob("*.html"):
        for href in re.findall(r'href="([^"]+)"', html.read_text("utf-8")):
            if href.startswith(("http", "mailto:", "#")):
                continue
            target = (html.parent / href).resolve()
            if not (target.exists() or target.is_dir()):
                broken.append((html.name, href))
    assert broken == [], broken[:10]


def test_home_teaser_is_generated_not_hardcoded():
    site.build()
    home = (site.SITE / "index.html").read_text("utf-8")
    # The marker is preserved (idempotent) and a real work link was injected.
    assert site._TEASER_MARKER in home
    assert re.search(r'work/paper-\d+\.html', home)
