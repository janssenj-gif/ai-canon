# Adversarial review — pilot-v0.1

**GATE A (machinery): PASS** (0 blocking findings)

| check | severity | status | detail |
|---|---|---|---|
| reproducibility | CRITICAL | pass | rebuilt corpus_hash + rankings match the committed release |
| provenance_complete | CRITICAL | pass | every present metric carries source+provenance_url+retrieved_at |
| no_cross_domain | CRITICAL | pass | each ranking is a single domain |
| no_silent_imputation | CRITICAL | pass | missing metrics carry an explicit penalty |
| conflict_flag_surfaced | HIGH | pass | every ranked row exposes conflict_flag |
| coverage_declared | HIGH | pass | coverage.json present (174 metrics; gaps declared) |
| ranking_sanity | HIGH | pass | rows ordered by score desc with sequential ranks |
| scenario_divergence | INFO | observed | scenario orderings differ — divergence demonstrated |

## Reviewer note

This automated pass verifies the *machinery* (reproducibility, provenance, domain
isolation, no-imputation, conflict flags, declared coverage) and the substantive
divergence claim.

Two independent signals are now harvested — all-time `citation_count` and recent-
momentum `sustained_readership` — and the three weighting scenarios produce **different**
orderings, so the method's central claim is demonstrated rather than asserted. Coverage is
still partial (a second pass over OpenAlex's daily budget will fill the remaining papers),
and `library_holdings` / `syllabus_adoptions` await WorldCat / Open Syllabus CSV drops;
those are declared gaps, not silent zeros.

