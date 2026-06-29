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

### Not yet
Book metric harvesting (title collisions — deferred), CN verification toward 60–90,
the real Top-50 release builder + audit package, adversarial review (GATE A), public site.
