# Changelog

Append-only. Scoring-logic or weight changes must land with an entry here (rule 10).

## seed v0.3: Stage A skeleton + harvest layer (2026-06-29)

### Sprint 1 + CAN-07: method package & seed import
- Frozen ontology v0.2 in pydantic v2; context entities have no score field (structural).
- Deterministic, domain-isolated scorer; published missing-data penalty (factor 0.5);
  weights in `scenarios.yaml` (3 placeholder weightings).
- ER stub: no auto-merge < 0.95; Aggarwal != Nielsen.
- Imported seeds: 573 books / 162 papers / 183 persons / 132 orgs / 90 platforms;
  250 descriptions; 573 categorized_as + 172 authored_by edges; Trap conflict-flagged.

### Sprint 2: harvest layer (CAN-09 / CAN-10 / CAN-12)
- `data/raw/` write-once store with per-source sha256 manifest (rule 6).
- OpenAlex harvester: live fetch into the write-once cache; metrics derived from the
  cached snapshot (offline-deterministic); no match / offline => declared gap, never imputed.
- Manual CSV-drop path (WorldCat / Open Syllabus): each row carries provenance or fails.
- `canon.harvest.assemble`: derives + validates + dedupes metrics (highest confidence wins)
  into `data/resolved/metrics.json` with a `coverage.json` report.
- Scorer gains `--corpus` mode: ranks real works that have harvested evidence; works
  without evidence are an honestly-declared coverage gap, not a fabricated zero.

### Sprint 3: release builder, audit package, adversarial review (CAN-15/16/17)
- `canon.release`: frozen release under `data/releases/<version>/`: Top-50 per
  (domain, scenario), full per-work breakdowns, divergence summary, a `Release`
  governance record with a deterministic `corpus_hash` (date is metadata, not hashed),
  coverage.json, and REPRODUCE.md. `--verify` rebuilds and asserts bit-identical (rule 3).
- `canon.redteam`: adversarial-review harness: reproducibility, provenance completeness,
  domain isolation, no-imputation, conflict-flag surfacing, declared coverage, ranking
  sanity, divergence honesty → `reports/red_team_findings.md` + a GATE-A verdict.
- **Pilot release `pilot-v0.1`: GATE A PASS (substantive)**: 0 blocking findings; reproducible.
- Second independent signal derived from the SAME cached OpenAlex snapshot (no new network):
  `sustained_readership` = citations in 2023-2025 (recent momentum), distinct from all-time
  `citation_count`. Assembled 174 metrics (88 citation_count + 86 sustained_readership).
- With two signals the three scenarios now produce **different orderings**
  (`scenario_divergence: observed`). The method's central claim is demonstrated, not merely asserted.
- Adversarial loop ran the full two iterations: iteration 1 flagged a stale single-metric
  `ranking_sanity` check (false positive); fixed to assert composite-score monotonicity; iteration 2 clean.
- Still-declared gaps: `library_holdings` / `syllabus_adoptions` await WorldCat / Open Syllabus CSV
  drops; ~74 papers await the next OpenAlex daily-budget window.

### Stage C: public site (CAN-21..25)
- `canon.export_site`: static generator (no framework, no JS deps, no tracker code) emits
  `site/` from the release JSON + seeds: Canon-50 (3 scenario views), per-work breakdown
  pages (the trust surface: every metric + provenance + missing-data penalty), papers shelf,
  method, challenges, changelog, and a downloadable audit package under `site/audit/`.
- The approved homepage (`site/index.html`) is wired to the live pages; its Canon-50 teaser
  is GENERATED (top-3 injected by the builder, idempotent) so the manifesto never carries
  hand-typed ranking data that can drift.
- 59 pages, 621 internal links (0 broken), verified rendering in-browser. Deploy target:
  `apparens.nl/ai-canon/` (Cloudflare Pages, static).

### Design pass: align to apparens.nl + house style
- Generated chrome rewritten to mirror `apparens-design-system.css`: deep-blue fixed nav with
  the white Apparens logo + serif wordmark, white body, orange `#B8430A`, DM Serif + DM Sans.
- The homepage is now GENERATED too (page_home), in the same design, so the whole site is
  visually consistent and rebuilds from one place. Its Canon-50 teaser is the live top-3.
- House style: no em-dashes in any site copy (enforced by a test).

### Acceptance audit response (decisions 1 to 6)
- **Library shipped** (`library.html`): all 573 candidate books, filterable by category / language /
  provenance, descriptions where written and "Description pending" otherwise, conflict-of-interest flag
  shown inline, labelled candidacy not canonical. Books are curated and browsable but not yet scored.
- **Context shelves shipped**: `voices.html` (183), `organizations.html` (132), `platforms.html` (90),
  grouped by category, alphabetical within category, labelled "described, never ranked" (no score).
- Nav reordered so the Library leads: the reference library is the primary surface, the ranking is one view.
- Verbatim positioning line on the home page; verbatim humility clause on the Canon-50 and every per-work
  page; significance lines added to the papers shelf.
- Open data: the audit page now offers JSON and CSV for the full corpus (books + papers + context).
- **Declared deferrals** (stated on the method page, not silently stubbed): per-ecosystem normalization
  (rule 5) activates only when more than one ecosystem enters a scored domain, so the site makes no
  worldwide / present-tense multilingual claim and the Chinese spine (28 works) is a declared gap; a fuller
  longevity proxy (holdings over time, editions, availability); and book scoring. The pilot ranks papers
  only, behind honest framing, and that scored view passed GATE A.
- House style enforced at the render boundary: even verbatim seed text shows no em-dashes; a test fails
  the build on any em-dash in generated HTML.
- **Self-contained audit bundle (decision 3):** `canon.release` now emits `audit-bundle.zip`, a
  byte-deterministic archive carrying the pipeline code, weights, pinned data snapshot, release outputs,
  and a one-command `reproduce.sh`. Verified: extracted into a clean directory with no repo, it rebuilds
  the release and reports corpus_hash MATCH. This is what makes the package archival and time-invariant.

### Security hardening to the app's bar (v1.2, the [S##] guardrails)
Derived from the AI Control Index app's posture and adapted for a static site.
- Strict CSP in `site/_headers`: `default-src 'none'`, no `unsafe-inline` / `unsafe-eval`,
  plus X-Content-Type-Options, Referrer-Policy, X-Frame-Options DENY, COOP, CORP,
  Permissions-Policy, HSTS. [S5]
- All CSS and JS externalized to `site/assets/` so the strict CSP holds; no inline script or
  style remains in any page. [S6]
- Self-hosted the DM fonts (reused the owner's licensed woff2): zero third-party requests,
  no Google Fonts. [S7]
- Output safety: `esc()` escapes quotes too; `safe_url()` scheme-sanitizes data-derived hrefs
  (javascript:/data: collapse to `#`); adversarial XSS fixtures prove hostile titles,
  descriptions, and URLs cannot become markup or script. [S8]
- `scripts/static-gate.sh` runs all 13 guardrails [S0]-[S12]; CI runs the gate; [S12] fails the
  build if ARCHITECTURE.md and the checks drift. ARCHITECTURE.md added with the [S##] system.
- 38 tests (8 security). The question behind this: if a million experts probe it, does it hold.

### Not yet
Book metric harvesting (title collisions: deferred), CN verification toward 60-90,
more harvested metrics (next OpenAlex daily window + WorldCat/Open Syllabus drops),
Zenodo DOI for the method note, deploy to Cloudflare Pages.
