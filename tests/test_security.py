"""Adversarial output-safety tests.

The public site is static, so the attack surface is what an attacker can get into
the generated HTML through the corpus data (titles, descriptions, names, URLs).
These tests assume a hostile contributor and assert the generator neutralizes it:
no untrusted field can become markup or script. If a million experts probe the
site, this is the property that has to hold.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from canon import export_site as site
from canon.export_site import esc, page_library, page_work, safe_url

_REL = Path(__file__).resolve().parents[1] / "data" / "releases" / site.VERSION

XSS = '<script>alert(1)</script>'
ATTR = '"><img src=x onerror=alert(1)>'


def test_esc_neutralizes_markup_and_quotes():
    out = esc(XSS)
    assert "<script>" not in out and "&lt;script&gt;" in out
    q = esc(ATTR)
    assert '"' not in q and "<img" not in q  # quote + angle brackets escaped


def test_safe_url_blocks_dangerous_schemes():
    for bad in ["javascript:alert(1)", "JavaScript:alert(1)", "data:text/html,<script>",
                "vbscript:msgbox", "  javascript:alert(1)"]:
        assert safe_url(bad) == "#", bad


def test_safe_url_allows_safe_and_relative():
    assert safe_url("https://openalex.org/W1") == "https://openalex.org/W1"
    assert safe_url("mailto:office@apparens.nl") == "mailto:office@apparens.nl"
    assert safe_url("work/paper-0001.html") == "work/paper-0001.html"


def _malicious_book():
    return {
        "id": "book-x", "canonical_title": XSS, "language": "en", "year": 2020,
        "work_type": "book", "conflict_flag": False,
        "editorial": {"author": ATTR, "category": "X", "source": "S",
                      "desc_confidence": "low", "description": f"hi {XSS}"},
    }


def test_library_escapes_hostile_corpus_fields():
    html = page_library([_malicious_book()])
    assert "<script>alert(1)" not in html
    assert "onerror=alert(1)>" not in html  # the raw attribute payload must not survive
    assert "&lt;script&gt;" in html         # it is present, but escaped


def test_work_page_sanitizes_javascript_provenance():
    per = {"academic": {"work_id": "paper-x", "canonical_title": "T", "work_type": "paper",
                        "scenario": "academic", "score": 0.1, "conflict_flag": False,
                        "components": [{"metric": "citation_count", "status": "present",
                                        "value": 1.0, "normalized": 1.0, "weight": 0.5,
                                        "contribution": 0.5, "source": "X", "confidence": "high",
                                        "provenance_url": "javascript:alert(1)"}]}}
    papers = {"paper-x": {"canonical_title": "T", "year": 2020, "conflict_flag": False,
                          "editorial": {"authors": "A", "significance": "S"}}}
    html = page_work("paper-x", per, papers)
    assert "javascript:" not in html
    assert 'href="#"' in html  # the dangerous scheme collapsed to a safe anchor


# --- the static-site security posture (mirrors the app's _headers + CSP) ------


@pytest.mark.skipif(not (_REL / "release.json").exists(), reason="no release built")
def test_headers_file_has_strict_csp_and_security_headers():
    site.build()
    h = (site.SITE / "_headers").read_text("utf-8")
    csp = next(line for line in h.splitlines() if "Content-Security-Policy" in line)
    # No unsafe-inline / unsafe-eval anywhere; default denies; framing blocked.
    assert "unsafe-inline" not in csp and "unsafe-eval" not in csp
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp and "object-src 'none'" in csp
    for header in ("X-Content-Type-Options: nosniff", "Referrer-Policy: no-referrer",
                   "X-Frame-Options: DENY", "Strict-Transport-Security",
                   "Cross-Origin-Opener-Policy: same-origin", "Permissions-Policy"):
        assert header in h, header


@pytest.mark.skipif(not (_REL / "release.json").exists(), reason="no release built")
def test_no_inline_script_or_style_survives_in_html():
    site.build()
    for html in site.SITE.rglob("*.html"):
        text = html.read_text("utf-8")
        assert "<style" not in text, f"inline style in {html.name}"
        # inline script BLOCK (content between tags) would break the CSP; src= is fine
        assert not re.search(r"<script(?![^>]*\ssrc=)[^>]*>", text), f"inline script in {html.name}"


@pytest.mark.skipif(not (_REL / "release.json").exists(), reason="no release built")
def test_no_third_party_requests_in_pages_or_css():
    site.build()
    targets = list(site.SITE.rglob("*.html")) + [site.SITE / "assets" / "canon.css",
                                                 site.SITE / "assets" / "fonts.css"]
    for f in targets:
        text = f.read_text("utf-8")
        for bad in ("googleapis", "gstatic", "//fonts.", "cdn.", "googletagmanager"):
            assert bad not in text, f"{bad} referenced in {f.name}"
