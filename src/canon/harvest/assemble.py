"""Assemble harvested + dropped evidence into data/resolved/metrics.json.

Deterministic: derives metrics from the write-once OpenAlex cache and any CSV
drops, validates every row against schema.Metric, dedupes by (work_id,
metric_name) keeping the highest-confidence row (ties: first by source name), and
writes a sorted metrics file plus a coverage report. No network here — assembly
runs entirely off the pinned cache, so it is reproducible.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..raw import RAW_DIR
from ..schema import Metric
from . import csv_drop, openalex

_RESOLVED = Path(__file__).resolve().parents[3] / "data" / "resolved"
_CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def _openalex_metrics() -> tuple[list[dict], list[dict]]:
    metrics, gaps = [], []
    for paper in openalex.load_papers():
        resp = openalex.fetch(paper, allow_network=False)
        out = openalex.parse(paper, resp)
        metrics.extend(out["metrics"])
        for g in out["gaps"]:
            gaps.append({"work_id": paper["id"], "metric": g["metric"], "reason": g["reason"]})
    return metrics, gaps


def _dedupe(metrics: list[dict]) -> list[dict]:
    best: dict[tuple[str, str], dict] = {}
    for m in metrics:
        key = (m["work_id"], m["metric_name"])
        incumbent = best.get(key)
        if incumbent is None:
            best[key] = m
            continue
        new_rank = _CONFIDENCE_RANK.get(m["confidence"], 0)
        old_rank = _CONFIDENCE_RANK.get(incumbent["confidence"], 0)
        if new_rank > old_rank or (new_rank == old_rank and m["source"] < incumbent["source"]):
            best[key] = m
    return list(best.values())


def assemble() -> dict:
    oa_metrics, gaps = _openalex_metrics()
    drop_metrics = csv_drop.load_drops(RAW_DIR)

    raw_metrics = oa_metrics + drop_metrics
    # Validate every row through the schema (rule 2 provenance enforced here).
    validated = [Metric(**m).model_dump(mode="json") for m in raw_metrics]
    deduped = _dedupe(validated)
    deduped.sort(key=lambda m: (m["work_id"], m["metric_name"]))

    _RESOLVED.mkdir(parents=True, exist_ok=True)
    (_RESOLVED / "metrics.json").write_text(
        json.dumps(deduped, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    by_metric: dict[str, int] = {}
    for m in deduped:
        by_metric[m["metric_name"]] = by_metric.get(m["metric_name"], 0) + 1
    coverage = {
        "metrics_total": len(deduped),
        "by_metric_name": dict(sorted(by_metric.items())),
        "openalex_gaps": len(gaps),
        "csv_drop_rows": len(drop_metrics),
    }
    (_RESOLVED / "coverage.json").write_text(
        json.dumps({**coverage, "gaps": gaps}, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(coverage, indent=2))
    return coverage


if __name__ == "__main__":
    assemble()
