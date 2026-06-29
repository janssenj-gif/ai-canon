"""Sprint 3 — release builder, reproducibility, and adversarial review (CAN-15/16/17)."""

from __future__ import annotations

from pathlib import Path

import pytest

from canon import redteam
from canon import release as rel

_METRICS = Path(__file__).resolve().parents[1] / "data" / "resolved" / "metrics.json"

pytestmark = pytest.mark.skipif(
    not _METRICS.exists(), reason="no assembled metrics — run `make assemble` first"
)


def test_corpus_hash_is_stable_across_builds():
    a = rel._build_payload("test", "2026-06-29")["corpus_hash"]
    b = rel._build_payload("test", "2099-01-01")["corpus_hash"]  # date must not affect hash
    assert a == b


def test_build_then_verify_reproduces():
    rel.build()
    assert rel.verify() is True


def test_redteam_gate_a_machinery_passes():
    rel.build()
    summary = redteam.review()
    assert summary["gate_a_machinery"] == "PASS"
    assert summary["blocking_findings"] == 0
    # The single-metric divergence limitation must be DECLARED, not hidden.
    div = next(f for f in summary["findings"] if f["check"] == "scenario_divergence")
    assert div["status"] in ("declared-limitation", "observed")
