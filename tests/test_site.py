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


def test_build_emits_home_core_and_work_pages():
    summary = site.build()
    for name in ("index.html", "canon-50.html", "papers.html", "method.html",
                 "challenges.html", "changelog.html", "data.html"):
        assert (site.SITE / name).exists(), name
    assert summary["work_pages"] > 0


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


def test_home_is_generated_with_live_teaser():
    site.build()
    home = (site.SITE / "index.html").read_text("utf-8")
    # The homepage is generated in the shared design and links a real work page.
    assert re.search(r'work/paper-\d+\.html', home)
    assert 'class="brand"' in home  # the apparens-style nav


def test_no_em_dashes_anywhere_in_site():
    site.build()
    offenders = [h.name for h in site.SITE.rglob("*.html") if "—" in h.read_text("utf-8")]
    assert offenders == [], offenders


def test_accessibility_invariants():
    """[S13] Static a11y guardrail. The full Axe pass is clean; this keeps the
    structural prerequisites from regressing without a browser in CI: a language,
    exactly one h1, alt text on every image, and no skipped heading levels."""
    site.build()
    problems = []
    for html in site.SITE.rglob("*.html"):
        t = html.read_text("utf-8")
        if '<html lang="' not in t:
            problems.append(f"{html.name}: missing lang")
        if t.count("<h1") != 1:
            problems.append(f"{html.name}: {t.count('<h1')} h1 (want 1)")
        for img in re.findall(r"<img\b[^>]*>", t):
            if "alt=" not in img:
                problems.append(f"{html.name}: img without alt")
        levels = [int(m) for m in re.findall(r"<h([1-6])\b", t)]
        for prev, cur in zip(levels, levels[1:]):
            if cur > prev + 1:
                problems.append(f"{html.name}: heading jump h{prev}->h{cur}")
                break
    assert problems == [], problems
