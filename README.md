# The AI Canon

A free, method-backed reference library for AI knowledge. It ranks **texts, not
people**. It invites correction. It sells nothing.

> Nothing is for sale. Nothing is hidden. Nothing is final.

The **library is the product; the method is the soul.** Any Top-N list is one
*view* over the data. This repository is the reproducible pipeline behind it.
The full strategy, the frozen ontology, and the build plan live in
[`docs/AI_Canon_MASTER_BUILD.md`](docs/AI_Canon_MASTER_BUILD.md); the project
rules are in [`CLAUDE.md`](CLAUDE.md).

## Status

Stage A skeleton + seed import (Sprint 1 + CAN-07). The deterministic scorer,
the frozen ontology, entity-resolution guards, and the full seed corpus are in
place. The pilot Top-50, harvesters, and the public site come in later stages.

## Quickstart

```bash
python3.12 -m venv .venv
make install        # pip install deps into .venv

make ingest         # import the 3 seed workbooks -> data/seeds/*.json
make harvest        # fetch OpenAlex citations -> write-once cache data/raw/openalex/
make assemble       # derive + validate + dedupe metrics -> data/resolved/metrics.json
make score-papers   # rank the papers domain from real harvested evidence
make release        # build the frozen release data/releases/pilot-v0.1/
make verify-release # rebuild + assert corpus_hash and rankings are bit-identical
make redteam        # adversarial review -> reports/red_team_findings.md + GATE-A verdict
make site           # generate the static public site into site/
make score          # deterministically score the fixture corpus
make test           # run the constitutional test suite
make guard          # verify no ad/affiliate/tracker code (rule 1)
```

`make site` emits the public site (Canon-50, per-work breakdown pages, method, challenges,
changelog, downloadable audit package) from the release JSON — static HTML, no framework,
no trackers. Deploy target: `apparens.nl/ai-canon/` on Cloudflare Pages.

`harvest` hits the network once and caches each response under `data/raw/openalex/`
(write-once); `assemble` and every later run derive metrics from that pinned cache
with no network, so the pipeline is reproducible. A work with no harvested metric
is a declared coverage gap (see `data/resolved/coverage.json`), never a fabricated zero.

> OpenAlex meters a small **free daily budget** (resets midnight UTC). The harvest
> is cached and resumable: if a run hits `429 Insufficient budget`, just re-run
> `make harvest` on a later day — cached papers are skipped and only the gaps are
> fetched. Current snapshot: **88 / 162 papers** have citations; the rest are
> declared gaps that fill on subsequent daily runs.

The pipeline is run with `PYTHONPATH=src` (the `Makefile` sets it) rather than an
editable install — `make` targets are the canonical entry points. To run a module
directly: `PYTHONPATH=src .venv/bin/python -m canon.ingest`. `pytest` needs no
`PYTHONPATH` (it reads `pythonpath = src` from `pyproject.toml`).

> Note: `make ingest` reads the source workbooks from `~/Desktop/files` (see the
> paths at the top of `src/canon/ingest.py`); the generated JSON in `data/seeds/`
> is committed, so tests and scoring run without them.

## What the pipeline guarantees

- **Deterministic**: same inputs + scenario produce bit-identical ranks.
- **Provenance on every number**: a metric without source, date, or url is rejected.
- **No silent imputation**: missing evidence is recorded and penalized by rule.
- **Domains never cross-rank**: a standard is never ranked against a monograph.
- **People are never scored**: context entities have no score field, structurally.
- **No ads, affiliates, or trackers**: enforced in CI.

## Security and the ship gate

The public site is static and hardened to the standard of the Apparens app: a strict
Content-Security-Policy (no inline script or style), self-hosted fonts (zero third-party
requests), HTML escaping and URL-scheme sanitization with adversarial tests, and a clean
axe-core accessibility pass. Every guardrail is numbered `[S0]` to `[S13]` in
[`ARCHITECTURE.md`](ARCHITECTURE.md) and enforced by `make gate` (`scripts/static-gate.sh`);
`[S12]` fails the build if the document and the checks drift.

## Cite this work

The method is documented in [`docs/method-note.md`](docs/method-note.md) (Corpus Cognitivum),
licensed CC BY 4.0. A DOI is minted on release via Zenodo:

<!-- After the first Zenodo release, replace XXXXXXX with the concept DOI and uncomment: -->
<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX) -->

> Janssen, J. (2026). *The AI Canon: a method for auditable knowledge curation (Corpus
> Cognitivum).* Apparens public research initiative. Version 1.0.

See [`CITATION.cff`](CITATION.cff) for machine-readable citation metadata.
