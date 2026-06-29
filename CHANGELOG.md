# Changelog

Append-only. Scoring-logic or weight changes must land with an entry here (rule 10).

## seed v0.3 — Stage A skeleton + harvest layer (2026-06-29)

### Sprint 1 + CAN-07 — method package & seed import
- Frozen ontology v0.2 in pydantic v2; context entities have no score field (structural).
- Deterministic, domain-isolated scorer; published missing-data penalty (factor 0.5);
  weights in `scenarios.yaml` (3 placeholder weightings).
- ER stub: no auto-merge < 0.95; Aggarwal != Nielsen.
- Imported seeds: 573 books / 162 papers / 183 persons / 132 orgs / 90 platforms;
  250 descriptions; 573 categorized_as + 172 authored_by edges; Trap conflict-flagged.

### Sprint 2 — harvest layer (CAN-09 / CAN-10 / CAN-12)
- `data/raw/` write-once store with per-source sha256 manifest (rule 6).
- OpenAlex harvester: live fetch into the write-once cache; metrics derived from the
  cached snapshot (offline-deterministic); no match / offline => declared gap, never imputed.
- Manual CSV-drop path (WorldCat / Open Syllabus): each row carries provenance or fails.
- `canon.harvest.assemble`: derives + validates + dedupes metrics (highest confidence wins)
  into `data/resolved/metrics.json` with a `coverage.json` report.
- Scorer gains `--corpus` mode: ranks real works that have harvested evidence; works
  without evidence are an honestly-declared coverage gap, not a fabricated zero.

### Sprint 3 — release builder, audit package, adversarial review (CAN-15/16/17)
- `canon.release`: frozen release under `data/releases/<version>/` — Top-50 per
  (domain, scenario), full per-work breakdowns, divergence summary, a `Release`
  governance record with a deterministic `corpus_hash` (date is metadata, not hashed),
  coverage.json, and REPRODUCE.md. `--verify` rebuilds and asserts bit-identical (rule 3).
- `canon.redteam`: adversarial-review harness — reproducibility, provenance completeness,
  domain isolation, no-imputation, conflict-flag surfacing, declared coverage, ranking
  sanity, divergence honesty → `reports/red_team_findings.md` + a GATE-A verdict.
- **Pilot release `pilot-v0.1`: GATE A PASS (substantive)** — 0 blocking findings; reproducible.
- Second independent signal derived from the SAME cached OpenAlex snapshot (no new network):
  `sustained_readership` = citations in 2023–2025 (recent momentum), distinct from all-time
  `citation_count`. Assembled 174 metrics (88 citation_count + 86 sustained_readership).
- With two signals the three scenarios now produce **different orderings** —
  `scenario_divergence: observed`. The method's central claim is demonstrated, not merely asserted.
- Adversarial loop ran the full two iterations: iteration 1 flagged a stale single-metric
  `ranking_sanity` check (false positive); fixed to assert composite-score monotonicity; iteration 2 clean.
- Still-declared gaps: `library_holdings` / `syllabus_adoptions` await WorldCat / Open Syllabus CSV
  drops; ~74 papers await the next OpenAlex daily-budget window.

### Not yet
Book metric harvesting (title collisions — deferred), CN verification toward 60–90,
multi-metric harvest to demonstrate scenario divergence, public site (Stage C).
