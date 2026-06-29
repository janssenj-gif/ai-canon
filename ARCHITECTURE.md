# The AI Canon, architecture

*Single source of truth for how the Canon is built, served, and kept safe. Mirrors the
discipline of the AI Control Index app: every hardening guardrail is numbered `[S##]`,
every `[S##]` has a check in `scripts/static-gate.sh`, and the gate fails on drift between
this document and the checks.*

North star: **Nothing is for sale. Nothing is hidden. Nothing is final.**

---

## Version history

> **v1.2 (2026-06-29)** Security hardening to the app's bar. Externalized all CSS/JS so the
> CSP forbids inline script and style (`[S5]`, `[S6]`); self-hosted the DM fonts so there is
> zero third-party request (`[S7]`); added `_headers` with a strict `default-src 'none'` CSP
> and the full security-header set; added URL-scheme sanitization and adversarial XSS tests
> (`[S8]`); introduced the `[S##]` guardrail system, `scripts/static-gate.sh`, and this
> document. Gate: 13 guardrails, 38 tests.

> **v1.1 (2026-06-29)** Acceptance-audit response: shipped the Library and the three context
> shelves (the reference library is the primary surface), verbatim positioning and humility
> clauses, declared deferrals, and the self-contained reproducible audit bundle.

> **v1.0 (2026-06-29)** Stages A through C: frozen ontology, deterministic scorer, OpenAlex
> harvest, GATE-A release, and the static public site generated from the release JSON.

---

## What it is

A free, public, method-backed reference library of the texts that define AI. The library is
the product; the method is the soul; any ranking is one view over the data. It ranks texts,
never people. See `docs/AI_Canon_MASTER_BUILD.md` for the full strategy and frozen ontology.

## Principles

1. Evidence before assertion. Every number carries its provenance or it does not exist.
2. The method is public and reproducible. A stranger can rebuild any release.
3. People are context, never contestants (structural: context entities have no score field).
4. Honesty about coverage. Gaps are declared, never zero-filled or invented.
5. No commercial influence, ever. No ads, affiliates, sponsorship, tracking, or cookies.
6. Static by construction. No backend, no database, nothing to leak or inject.
7. House style: no em-dashes in copy.

---

## Technical architecture

- **Language / stack:** Python 3.12, pydantic v2. Flat files + Git are the database. No ORM,
  no framework. The public site is plain static HTML/CSS/JS.
- **Pipeline modules** (`src/canon/`): `schema.py` (frozen ontology v0.2), `score.py`
  (deterministic, domain-isolated scorer), `resolve.py` (entity-resolution guards),
  `ingest.py` (seed import), `harvest/` (OpenAlex harvester, CSV-drop, assemble), `release.py`
  (release builder + self-contained audit bundle), `redteam.py` (adversarial review),
  `export_site.py` (static site generator), `raw.py` (write-once harvest store).
- **Build:** `make ingest | harvest | assemble | release | site`. The site is generated
  deterministically from `data/releases/<version>/` + `data/seeds/`. CSS and JS are emitted as
  external files (`site/assets/canon.css`, `site/assets/canon.js`); fonts are self-hosted
  (`site/assets/fonts/`, `site/assets/fonts.css`).
- **Serving:** Cloudflare Pages, static, deploy root = `site/` only (no source, no data
  pipeline, no secrets ship). `site/_headers` carries the CSP and security headers.
- **The only inbound data path** is the challenge mailbox (`office@apparens.nl`). There is no
  form, endpoint, or write path on the public site.

## Page map

`index.html` (manifesto + live Canon-50 teaser), `library.html` (573 books, filterable),
`canon-50.html` (3 scenario views), `work/<id>.html` (per-work trust surface),
`papers.html`, `voices.html` / `organizations.html` / `platforms.html` (context shelves,
described never ranked), `method.html`, `challenges.html`, `changelog.html`, `data.html`
(audit downloads + reproduce), `press.html`, `share.html`.

---

## Security posture and guardrails

The static threat model: an attacker's only lever is data that reaches the generated HTML
(titles, descriptions, names, URLs), plus the browser delivery surface. Each guardrail below
is enforced by `scripts/static-gate.sh`.

- **[S0] Syntax.** All Python modules compile (`py_compile`).
- **[S1] Test suite.** The full pytest suite is green (schema, scorer, ER, harvest, release,
  site, security).
- **[S2] No commercial code.** No ad / affiliate / tracker code signatures in `src/` or
  `site/` (`scripts/guard_no_trackers.sh`).
- **[S3] No em-dashes** in any generated HTML (house style).
- **[S4] Link integrity.** Zero broken internal links across the generated site.
- **[S5] Strict CSP + security headers.** `site/_headers` sets `default-src 'none'` with no
  `unsafe-inline` / `unsafe-eval`, plus `frame-ancestors 'none'`, `object-src 'none'`,
  X-Content-Type-Options, Referrer-Policy, X-Frame-Options, COOP, CORP, Permissions-Policy, HSTS.
- **[S6] No inline script or style.** All CSS/JS is external `'self'`, so the strict CSP holds.
- **[S7] No third-party requests.** Fonts and assets are self-hosted; no Google Fonts, CDN, or
  tracker origin appears in any page or stylesheet.
- **[S8] Output safety.** Every data field is HTML-escaped at the render boundary (`esc`,
  `quote=True`); data-derived hrefs are scheme-sanitized (`safe_url`: only http/https/mailto,
  else `#`). Adversarial XSS fixtures assert hostile titles, descriptions, and `javascript:`
  URLs cannot become markup or script.
- **[S9] Deterministic reproduction.** `release --verify` rebuilds the release and asserts a
  bit-identical `corpus_hash`.
- **[S10] Self-contained audit bundle.** `audit-bundle.zip` carries code + weights + pinned
  data + reproduce script; it rebuilds the release offline with no repo.
- **[S11] Clean deployable.** Only static assets ship in `site/`; no `.py`, `.env`, secrets,
  or build artifacts.
- **[S12] Architecture drift.** Every `[S##]` named here has a corresponding gate check; the
  gate fails if this document and the checks diverge.
- **[S13] Accessibility.** A full axe-core pass across all page types is clean (0 violations).
  A static lint keeps the prerequisites from regressing in CI without a browser: every page
  declares a language, has exactly one h1, gives every image alt text, and never skips a
  heading level. Body links are underlined (distinguishable without color) and footer text
  meets the contrast threshold.

## Non-functional requirements

Reproducible builds; static-first; full Unicode (CJK titles render via system fallback;
romanization is a declared gap); core reading works with no JavaScript (filtering enhances);
no browser storage (no localStorage / sessionStorage / cookies); the corpus is consumable as
open JSON and CSV without the site.

## Funding and independence

No advertising, no affiliate links, no sponsored placement, no paid inclusion, ever.
CI-enforced (`[S2]`). Apparens-authored works carry `conflict_flag: true`, surfaced in the data
and on the page, scored by the same rules with no exemption and no boost.
