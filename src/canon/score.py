"""Deterministic, domain-isolated scorer with a published missing-data penalty.

Constitutional guarantees implemented here:
  * Rule 3 — determinism: identical inputs + scenario -> bit-identical output.
              No randomness, no dict-iteration-order dependence, fixed rounding,
              stable tie-break by work id.
  * Rule 4 — domains never cross-rank: ranking a mixed-work_type set raises
              CrossDomainError.
  * Rule 5 — per-ecosystem/per-domain normalization first: metrics are min-max
              normalized WITHIN the domain being ranked.
  * Rule 8 — no silent imputation: a scenario-weighted metric that a work lacks
              is recorded as `missing` and penalized by a published rule.
  * Rule 9 — weights live in scenarios.yaml, loaded here, never hard-coded.

A score is not a verdict on intrinsic worth. It is a transparent output of
declared evidence, weights, and missing-data rules at a release date.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import yaml

from .schema import Metric, Work

# Fixed precision keeps output reproducible across machines (rule 3).
_ROUND = 6

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCENARIOS_PATH = _REPO_ROOT / "scenarios.yaml"


class CrossDomainError(ValueError):
    """Raised when a caller tries to rank works of more than one work_type."""


def load_scenarios(path: Path | None = None) -> dict:
    with open(path or _SCENARIOS_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _scenario_config(scenarios_doc: dict, scenario: str) -> dict:
    try:
        cfg = scenarios_doc["scenarios"][scenario]
    except KeyError as exc:
        raise KeyError(f"unknown scenario: {scenario!r}") from exc
    return cfg


def _metrics_by_name(metrics: Iterable[Metric]) -> dict[str, Metric]:
    # If a metric repeats, the last-written wins; harvest dedup happens upstream.
    return {m.metric_name: m for m in metrics}


def _domain_minmax(
    works: list[Work],
    metrics_by_work: dict[str, list[Metric]],
    metric_names: list[str],
) -> dict[str, tuple[float, float]]:
    """Min/max per metric across the domain. Missing values do not contribute."""
    bounds: dict[str, tuple[float, float]] = {}
    for name in metric_names:
        values = [
            _metrics_by_name(metrics_by_work.get(w.id, [])).get(name).value
            for w in works
            if _metrics_by_name(metrics_by_work.get(w.id, [])).get(name) is not None
        ]
        if values:
            bounds[name] = (min(values), max(values))
    return bounds


def breakdown(
    work: Work,
    metrics: list[Metric],
    scenario: str,
    scenarios_doc: dict,
    bounds: dict[str, tuple[float, float]],
) -> dict:
    """The trust-surface record: exactly why this work scored what it scored.

    Returns final score plus, for every scenario-weighted metric, its value /
    source / retrieved_at / confidence / provenance_url, the weight applied, the
    normalized value, and any missing-data penalty — enough for a stranger to
    rebuild the number or challenge it.
    """
    cfg = _scenario_config(scenarios_doc, scenario)
    weights: dict[str, float] = cfg["weights"]
    penalty_factor: float = scenarios_doc.get("missing_data_penalty_factor", 0.0)

    by_name = _metrics_by_name(metrics)
    components: list[dict] = []
    score = 0.0

    # Sort metric names so the breakdown order is deterministic (rule 3).
    for name in sorted(weights):
        weight = weights[name]
        metric = by_name.get(name)
        if metric is None:
            penalty = round(weight * penalty_factor, _ROUND)
            score -= penalty
            components.append(
                {
                    "metric": name,
                    "status": "missing",
                    "weight": weight,
                    "missing_data_penalty": penalty,
                    "note": "recorded as missing; penalized by rule, never imputed",
                }
            )
            continue

        lo, hi = bounds.get(name, (metric.value, metric.value))
        normalized = 0.0 if hi == lo else (metric.value - lo) / (hi - lo)
        contribution = round(weight * normalized, _ROUND)
        score += contribution
        components.append(
            {
                "metric": name,
                "status": "present",
                "value": metric.value,
                "normalized": round(normalized, _ROUND),
                "weight": weight,
                "contribution": contribution,
                "source": metric.source,
                "retrieved_at": metric.retrieved_at.isoformat(),
                "confidence": metric.confidence,
                "provenance_url": metric.provenance_url,
            }
        )

    return {
        "work_id": work.id,
        "canonical_title": work.canonical_title,
        "work_type": work.work_type,
        "scenario": scenario,
        "score": round(score, _ROUND),
        "conflict_flag": work.conflict_flag,
        "components": components,
    }


def rank_within_domain(
    works: list[Work],
    metrics_by_work: dict[str, list[Metric]],
    scenario: str,
    scenarios_doc: dict | None = None,
) -> list[dict]:
    """Rank a single-domain set of works under a scenario.

    Raises CrossDomainError if the works are not all the same work_type
    (rule 4: a standard is never ranked against a monograph).
    """
    if not works:
        return []

    work_types = {w.work_type for w in works}
    if len(work_types) > 1:
        raise CrossDomainError(
            f"refusing to cross-rank work_types {sorted(work_types)} "
            "(rule 4: domains never cross-rank)"
        )

    scenarios_doc = scenarios_doc or load_scenarios()
    cfg = _scenario_config(scenarios_doc, scenario)
    metric_names = sorted(cfg["weights"])
    bounds = _domain_minmax(works, metrics_by_work, metric_names)

    rows = [
        breakdown(w, metrics_by_work.get(w.id, []), scenario, scenarios_doc, bounds)
        for w in works
    ]
    # Deterministic order: score desc, then work_id asc as a stable tie-break.
    rows.sort(key=lambda r: (-r["score"], r["work_id"]))
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return rows


def to_json(rows: list[dict]) -> str:
    """Canonical JSON serialization: sorted keys, fixed separators (rule 3)."""
    return json.dumps(rows, sort_keys=True, ensure_ascii=False, indent=2)


def _load_corpus_works(work_type: str) -> list:
    from .schema import Work

    fname = {"book": "books.json", "paper": "papers.json"}[work_type]
    recs = json.loads((_REPO_ROOT / "data" / "seeds" / fname).read_text("utf-8"))
    return [
        Work(
            id=r["id"],
            canonical_title=r["canonical_title"],
            original_title=r.get("original_title"),
            language=r["language"],
            year=r.get("year"),
            work_type=r["work_type"],
            conflict_flag=r.get("conflict_flag", False),
        )
        for r in recs
    ]


def _load_corpus_metrics() -> dict[str, list]:
    from .schema import Metric

    path = _REPO_ROOT / "data" / "resolved" / "metrics.json"
    if not path.exists():
        return {}
    out: dict[str, list] = {}
    for m in json.loads(path.read_text("utf-8")):
        out.setdefault(m["work_id"], []).append(Metric(**m))
    return out


def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="The AI Canon deterministic scorer")
    parser.add_argument(
        "--fixtures", action="store_true", help="score the bundled fixture corpus"
    )
    parser.add_argument(
        "--corpus",
        action="store_true",
        help="score the real corpus (data/seeds + data/resolved/metrics.json)",
    )
    parser.add_argument("--scenario", default="academic")
    parser.add_argument("--work-type", default="book")
    parser.add_argument("--top", type=int, default=20, help="rows to print in --corpus mode")
    args = parser.parse_args(argv)

    if args.corpus:
        metrics_by_work = _load_corpus_metrics()
        # Only rank works that have at least one harvested metric; the rest are
        # an honestly-declared coverage gap, not a fabricated zero.
        works = [w for w in _load_corpus_works(args.work_type) if w.id in metrics_by_work]
        rows = rank_within_domain(works, metrics_by_work, args.scenario)
        print(f"# {args.work_type} domain — {args.scenario} — {len(rows)} works with evidence")
        print(to_json(rows[: args.top]))
        return 0

    if not args.fixtures:
        parser.error("pass --fixtures or --corpus")

    from . import fixtures

    works = fixtures.works_of_type(args.work_type)
    rows = rank_within_domain(works, fixtures.metrics_by_work(), args.scenario)
    print(to_json(rows))
    if rows:
        # Echo one full breakdown to stderr-free stdout for the trust surface.
        print("\n# full breakdown of rank 1:")
        print(json.dumps(rows[0], sort_keys=True, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
