"""Sprint 2 — harvest layer tests (CAN-09 / CAN-10 / CAN-12)."""

from __future__ import annotations

import pytest

from canon import raw
from canon.harvest import csv_drop
from canon.harvest.assemble import _dedupe
from canon.harvest.openalex import parse


# --- rule 6: data/raw is write-once ----------------------------------------


def test_raw_write_once_blocks_differing_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(raw, "RAW_DIR", tmp_path)
    raw.write_once("openalex", "x.json", "first")
    # identical re-write is an idempotent no-op
    raw.write_once("openalex", "x.json", "first")
    with pytest.raises(raw.RawImmutableError):
        raw.write_once("openalex", "x.json", "DIFFERENT")


# --- CAN-09: OpenAlex parse derives a metric or a declared gap, never imputes


def _resp(**over):
    result = {
        "id": "https://openalex.org/W2626778328",
        "display_name": "Attention Is All You Need",
        "publication_year": 2017,
        "cited_by_count": 120000,
        "counts_by_year": [
            {"year": 2025, "cited_by_count": 9000},
            {"year": 2024, "cited_by_count": 8000},
            {"year": 2023, "cited_by_count": 7000},
            {"year": 2018, "cited_by_count": 100},
        ],
    }
    result.update(over.pop("result", {}))
    base = {"results": [result]}
    base.update(over)
    return base


def _by_name(metrics):
    return {m["metric_name"]: m for m in metrics}


def test_openalex_parse_extracts_both_signals():
    paper = {"id": "paper-x", "canonical_title": "Attention Is All You Need", "year": 2017}
    out = parse(paper, _resp())
    by = _by_name(out["metrics"])
    assert by["citation_count"]["value"] == 120000.0
    assert by["citation_count"]["confidence"] == "high"
    # sustained_readership = sum of 2023+2024+2025 only (2018 excluded)
    assert by["sustained_readership"]["value"] == 24000.0
    assert by["citation_count"]["provenance_url"].startswith("https://openalex.org/")


def test_openalex_missing_counts_by_year_gaps_only_that_metric():
    paper = {"id": "paper-x", "canonical_title": "Attention Is All You Need", "year": 2017}
    out = parse(paper, _resp(result={"counts_by_year": []}))
    by = _by_name(out["metrics"])
    assert "citation_count" in by  # still present
    assert "sustained_readership" not in by
    assert any(g["metric"] == "sustained_readership" for g in out["gaps"])


def test_openalex_parse_offline_is_a_declared_gap():
    paper = {"id": "paper-x", "canonical_title": "Attention Is All You Need", "year": 2017}
    out = parse(paper, None)
    assert out["metrics"] == [] and out["gaps"]


def test_openalex_parse_no_match_is_a_gap_not_a_zero():
    paper = {"id": "paper-x", "canonical_title": "An Entirely Unrelated Title", "year": 1999}
    out = parse(paper, _resp())
    assert out["metrics"] == [] and out["gaps"]


# --- CAN-10: CSV drops carry provenance or fail loudly ----------------------

GOOD_CSV = (
    "work_id,metric_name,value,source,retrieved_at,confidence,provenance_url,license_note\n"
    "paper-0001,syllabus_adoptions,42,Open Syllabus,2026-06-29,medium,https://opensyllabus.org/x,derived\n"
)


def test_csv_drop_parses_valid_rows():
    rows = csv_drop.parse_csv_text(GOOD_CSV)
    assert len(rows) == 1 and rows[0]["value"] == 42.0


def test_csv_drop_rejects_missing_provenance_column():
    bad = "work_id,metric_name,value\npaper-0001,syllabus_adoptions,42\n"
    with pytest.raises(csv_drop.CsvDropError):
        csv_drop.parse_csv_text(bad)


def test_csv_drop_rejects_non_numeric_value():
    bad = GOOD_CSV.replace(",42,", ",lots,")
    with pytest.raises(csv_drop.CsvDropError):
        csv_drop.parse_csv_text(bad)


# --- assembly dedupe keeps the highest-confidence row -----------------------


def test_dedupe_prefers_higher_confidence():
    metrics = [
        {"work_id": "p1", "metric_name": "citation_count", "value": 1.0, "confidence": "low", "source": "B"},
        {"work_id": "p1", "metric_name": "citation_count", "value": 2.0, "confidence": "high", "source": "A"},
    ]
    out = _dedupe(metrics)
    assert len(out) == 1 and out[0]["confidence"] == "high" and out[0]["value"] == 2.0
