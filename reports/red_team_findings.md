# Adversarial review — pilot-v0.1

**GATE A (machinery): PASS** (0 blocking findings)

| check | severity | status | detail |
|---|---|---|---|
| reproducibility | CRITICAL | pass | rebuilt corpus_hash + rankings match the committed release |
| provenance_complete | CRITICAL | pass | every present metric carries source+provenance_url+retrieved_at |
| no_cross_domain | CRITICAL | pass | each ranking is a single domain |
| no_silent_imputation | CRITICAL | pass | missing metrics carry an explicit penalty |
| conflict_flag_surfaced | HIGH | pass | every ranked row exposes conflict_flag |
| coverage_declared | HIGH | pass | coverage.json present (88 metrics; gaps declared) |
| ranking_sanity | HIGH | pass | ranking order consistent with evidence |
| scenario_divergence | INFO | declared-limitation | scenarios share an ordering (only citation_count harvested) — declared in release.json; the method's divergence claim is NOT yet demonstrated and needs more metrics |

## Reviewer note

This automated pass verifies the *machinery* (reproducibility, provenance, domain
isolation, no-imputation, conflict flags, declared coverage). It is the first of the
two GATE-A iterations. The substantive claim — that the three weighting scenarios
produce *meaningfully different* canons — cannot be demonstrated on a single harvested
metric (citation_count). Demonstrating divergence requires harvesting library_holdings,
syllabus_adoptions, and sustained_readership, which is gated on OpenAlex's daily budget
and the WorldCat / Open Syllabus CSV drops. Until then the pilot is honest about being a
single-signal ranking, per the master doc's humility rule.

