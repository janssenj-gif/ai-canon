"""Stage C — static site generator (CAN-21..25).

Reads data/releases/<version>/ + data/seeds/ + scenarios.yaml + CHANGELOG.md and
emits plain, framework-free HTML into site/. The whole public site is generated
from the canonical JSON: there is no app server and no live database, so nothing
can leak or be injected (master doc, Part V). Output is deterministic.

Pages generated (alongside the approved site/index.html):
  canon-50.html          three scenario views; each rank links to its breakdown
  work/<id>.html         the per-work trust surface (every metric + provenance)
  papers.html            all 162 papers, honest about scored-vs-seed status
  method.html            the 8 rules, ontology, weighting scenarios, missing-data rule
  challenges.html        the challenge protocol + log (the differentiator; empty for now)
  changelog.html         rendered from CHANGELOG.md
  data.html              the downloadable audit package + one-command reproduce
  audit/                 copied release + seed JSON (openly downloadable)
"""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

import yaml

from . import METHOD_VERSION, ONTOLOGY_VERSION

_ROOT = Path(__file__).resolve().parents[2]
SITE = _ROOT / "site"
SEEDS = _ROOT / "data" / "seeds"
RELEASES = _ROOT / "data" / "releases"
VERSION = "pilot-v0.1"

NAV = [
    ("index.html", "Home"),
    ("canon-50.html", "Canon 50"),
    ("papers.html", "Papers"),
    ("method.html", "Method"),
    ("challenges.html", "Challenges"),
    ("changelog.html", "Changelog"),
    ("data.html", "Data & audit"),
]

# Mirrors the apparens.nl design system (apparens-design-system.css): deep-blue
# fixed nav with the white wordmark, white body, orange #B8430A accents, DM Serif
# Display headings, DM Sans body. Self-contained (no external CSS), per Part V.
_STYLE = """
:root{--deep:#051C2C;--navy:#0A2540;--mid:#1A3A5C;--white:#fff;--g100:#F5F5F5;
--g200:#EAEAEA;--g300:#D4D4D4;--g500:#6B6B6B;--g700:#333;--ice:#E8F0FE;--cream:#F5F0E8;
--orange:#B8430A;--orange-hover:#9E3908;--orange-dark:#E65710;--teal:#135975}
*{margin:0;padding:0;box-sizing:border-box}
html{font-size:18px;-webkit-font-smoothing:antialiased;scroll-behavior:smooth}
body{font-family:"DM Sans",-apple-system,BlinkMacSystemFont,sans-serif;color:var(--g700);
background:var(--white);line-height:1.5;padding-top:86px}
[id]{scroll-margin-top:96px}
.measure{max-width:1080px;margin:0 auto;padding:0 32px}
a{color:var(--orange);text-decoration:none}
a:hover{color:var(--orange-hover);text-decoration:underline}
:focus-visible{outline:2px solid var(--orange);outline-offset:2px}
/* ── fixed two-tier nav ── */
nav.top{position:fixed;top:0;left:0;right:0;z-index:100;background:var(--deep);
border-bottom:1px solid rgba(255,255,255,.08)}
nav.top .row1{max-width:1080px;margin:0 auto;padding:0 32px;height:50px;display:flex;
align-items:center;justify-content:space-between}
nav.top .brand{display:flex;align-items:center;gap:11px;text-decoration:none}
nav.top .brand img{height:26px;width:auto}
nav.top .brand b{color:#fff;font-family:"DM Serif Display",serif;font-weight:400;font-size:18px}
nav.top .row1 .out{color:var(--orange-dark);font-size:.82rem;text-decoration:none;font-weight:600}
nav.top .row2{max-width:1080px;margin:0 auto;padding:0 32px;height:38px;display:flex;
flex-wrap:wrap;align-items:center;gap:22px;border-top:1px solid rgba(255,255,255,.06)}
nav.top .row2 a{font-size:.82rem;color:rgba(255,255,255,.7);text-decoration:none}
nav.top .row2 a:hover{color:#fff}
nav.top .row2 a[aria-current=page]{color:#fff;border-bottom:2px solid var(--orange-dark);padding-bottom:2px}
/* ── header band ── */
header.h{background:var(--white);padding:44px 0 26px;border-bottom:1px solid var(--g200)}
.overline{font-size:.8rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--orange)}
h1{font-family:"DM Serif Display",serif;font-weight:400;font-size:clamp(2rem,5vw,3rem);
line-height:1.1;letter-spacing:-.02em;margin:10px 0;color:var(--deep)}
h2{font-family:"DM Serif Display",serif;font-weight:400;font-size:1.6rem;line-height:1.25;margin:34px 0 12px;color:var(--deep)}
h3{font-size:.8rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--orange);margin:24px 0 8px}
p{margin:10px 0;color:var(--g700)}main{padding:30px 0 70px}
.lead{font-size:1.125rem;color:var(--g500);line-height:1.7}
/* ── callout ── */
.note{background:var(--ice);border-left:3px solid var(--orange);padding:14px 20px;margin:20px 0;font-size:.95rem;color:var(--g700)}
.note.flag{background:#FCEEE6}
/* ── tables ── */
table{width:100%;border-collapse:collapse;margin:16px 0;font-size:.9rem}
th{text-align:left;font-size:.7rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
color:var(--g500);border-bottom:2px solid var(--navy);padding:9px 10px}
td{padding:9px 10px;border-bottom:1px solid var(--g200);vertical-align:top;color:var(--g700)}
tr:hover td{background:var(--g100)}
td.rank,td.num{font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--g500)}
td a{color:var(--deep);font-weight:500;text-decoration:none}td a:hover{color:var(--orange)}
.tag{font-size:.68rem;padding:2px 9px;border:1px solid var(--g300);border-radius:20px;color:var(--g500);white-space:nowrap}
.flag{color:var(--orange);font-weight:600}
.scn{margin:26px 0;border:1px solid var(--g200);border-radius:6px;background:var(--white);
box-shadow:0 1px 3px rgba(0,0,0,.05);padding:6px 22px 18px}
.scn h2{margin-top:18px}
.miss{color:var(--g500)}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.82rem;color:var(--g500)}
ol,ul{margin:10px 0 10px 22px}li{margin:6px 0}
/* ── footer ── */
footer{background:var(--deep);color:rgba(255,255,255,.6);padding:40px 0 34px;margin-top:40px;font-size:.85rem}
footer .measure{max-width:1080px}
footer a{color:rgba(255,255,255,.8)}footer a:hover{color:#fff}
footer .fine{font-size:.62rem;color:rgba(255,255,255,.3);line-height:1.7;margin-top:16px;
padding-top:14px;border-top:1px solid rgba(255,255,255,.08);max-width:820px}
"""


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def _nav(active: str, prefix: str) -> str:
    links = []
    for href, label in NAV:
        if href == "index.html":
            continue  # Home is the logo/wordmark
        cur = ' aria-current="page"' if href == active else ""
        links.append(f'<a href="{prefix}{href}"{cur}>{esc(label)}</a>')
    return f"""<nav class="top">
  <div class="row1">
    <a class="brand" href="{prefix}index.html"><img src="{prefix}apparens-logo-white.png" alt="Apparens" width="510" height="118"><b>The AI Canon</b></a>
    <a class="out" href="https://apparens.nl">Apparens.nl ↗</a>
  </div>
  <div class="row2">{"".join(links)}</div>
</nav>"""


def shell(active: str, kicker: str, title: str, body: str, *, depth: int = 0) -> str:
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} — The AI Canon</title>
<meta name="description" content="The AI Canon — a free, method-backed reference library for AI knowledge.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap" rel="stylesheet">
<style>{_STYLE}</style></head><body>
{_nav(active, prefix)}
<header class="h"><div class="measure"><span class="overline">{esc(kicker)}</span><h1>{esc(title)}</h1></div></header>
<main><div class="measure">{body}</div></main>
<footer><div class="measure">
<p>The AI Canon — an <a href="https://apparens.nl">Apparens</a> public research initiative · release <b style="color:#fff;font-weight:600">{esc(VERSION)}</b> · challenge anything: <a href="mailto:office@apparens.nl">office@apparens.nl</a></p>
<p style="margin-top:6px">Nothing is for sale. Nothing is hidden. Nothing is final.</p>
<p class="fine">No cookies · No third-party tracking · No ads, affiliates, or sponsored placement — ever. The site is generated statically from the canonical JSON; the only inbound data path is the challenge mailbox.</p>
</div></footer>
</body></html>
"""


def _write(rel_path: str, content: str) -> None:
    out = SITE / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


# --- data loaders -----------------------------------------------------------


def _load(path: Path):
    return json.loads(path.read_text("utf-8"))


def _papers_index() -> dict:
    return {p["id"]: p for p in _load(SEEDS / "papers.json")}


def _scenarios() -> dict:
    return yaml.safe_load((_ROOT / "scenarios.yaml").read_text("utf-8"))


# --- pages ------------------------------------------------------------------


def page_canon50(release: dict, rankings: dict, papers: dict) -> str:
    scn_doc = _scenarios()
    parts = [
        '<p class="note">Pilot release <b>%s</b>. This ranks the <b>papers</b> domain only — '
        "books carry no harvested metrics yet. Two signals are harvested (all-time citations and "
        "recent-citation momentum); coverage is partial and every gap is declared. A rank is not a "
        "verdict on worth — it is a transparent output of declared evidence, weights, and missing-data "
        "rules at this release date.</p>" % esc(VERSION)
    ]
    for scenario in sorted(scn_doc["scenarios"]):
        rows = rankings.get(f"paper__{scenario}", [])
        desc = scn_doc["scenarios"][scenario].get("description", "")
        body = [
            f'<div class="scn"><h2>{esc(scenario.replace("_", " ").title())}</h2>',
            f'<p class="mono">{esc(desc)}</p>',
            "<table><thead><tr><th>Rank</th><th>Paper</th><th>Year</th><th>Score</th><th>Evidence</th></tr></thead><tbody>",
        ]
        for r in rows:
            p = papers.get(r["work_id"], {})
            present = [c["metric"] for c in r["components"] if c.get("status") == "present"]
            ev = ", ".join(present) or "—"
            flag = ' <span class="flag" title="conflict of interest declared">⚑</span>' if r.get("conflict_flag") else ""
            body.append(
                f'<tr><td class="rank">{r["rank"]:03d}</td>'
                f'<td><a href="work/{esc(r["work_id"])}.html">{esc(p.get("canonical_title",""))}</a>{flag}</td>'
                f'<td class="num">{esc(p.get("year",""))}</td>'
                f'<td class="num">{r["score"]:.4f}</td>'
                f'<td class="mono">{esc(ev)}</td></tr>'
            )
        body.append("</tbody></table></div>")
        parts.append("".join(body))
    div = release.get("divergence", {}).get("paper", {})
    parts.append(
        f'<p class="note">{esc(div.get("note",""))} '
        f'Each rank links to its full score breakdown — every metric, its source, retrieval date, and weight.</p>'
    )
    return shell("canon-50.html", "Canon 50 · pilot", "The Canon 50", "".join(parts))


def page_work(work_id: str, per_scenario: dict, papers: dict) -> str:
    p = papers.get(work_id, {})
    ed = p.get("editorial", {})
    head = [
        f'<p class="mono">{esc(work_id)} · paper · {esc(p.get("year",""))}</p>',
        f'<p>{esc(ed.get("authors",""))}</p>',
    ]
    if ed.get("significance"):
        head.append(f'<p>{esc(ed["significance"])}</p>')
    if p.get("conflict_flag"):
        head.append('<p class="note flag">Conflict of interest declared for this work.</p>')
    blocks = ["".join(head)]
    for scenario in sorted(per_scenario):
        row = per_scenario[scenario]
        blocks.append(f'<h2>{esc(scenario.replace("_"," ").title())} — score {row["score"]:.4f}</h2>')
        rows = ["<table><thead><tr><th>Metric</th><th>Status</th><th>Value</th><th>Norm.</th>"
                "<th>Weight</th><th>Contribution</th><th>Source</th><th>Confidence</th><th>Provenance</th></tr></thead><tbody>"]
        for c in row["components"]:
            if c.get("status") == "present":
                prov = c.get("provenance_url", "")
                prov_a = f'<a href="{esc(prov)}">link</a>' if prov else "—"
                rows.append(
                    f'<tr><td class="mono">{esc(c["metric"])}</td><td>present</td>'
                    f'<td class="num">{esc(c.get("value",""))}</td><td class="num">{esc(c.get("normalized",""))}</td>'
                    f'<td class="num">{esc(c.get("weight",""))}</td><td class="num">{esc(c.get("contribution",""))}</td>'
                    f'<td>{esc(c.get("source",""))}</td><td>{esc(c.get("confidence",""))}</td><td>{prov_a}</td></tr>'
                )
            else:
                rows.append(
                    f'<tr class="miss"><td class="mono">{esc(c["metric"])}</td><td>missing</td>'
                    f'<td colspan="3">recorded as missing — penalized by rule, never imputed</td>'
                    f'<td class="num">−{esc(c.get("missing_data_penalty",""))}</td><td colspan="3">{esc(c.get("note",""))}</td></tr>'
                )
        rows.append("</tbody></table>")
        blocks.append("".join(rows))
    subject = f"Challenge rank: {work_id}"
    body = f"mailto:office@apparens.nl?subject={esc(subject)}"
    blocks.append(
        f'<p class="note">Disagree with this rank or a number? <a href="{body}">Challenge it</a> — '
        "with your evidence. Every challenge gets a public identifier and a published resolution.</p>"
    )
    return shell("canon-50.html", "Score breakdown", esc(p.get("canonical_title", work_id)),
                 "".join(blocks), depth=1)


def page_papers(papers: dict, metrics_by_work: set) -> str:
    rows = ["<p class=\"note\">All 162 seed papers. <b>Seed status means candidacy, not canonical "
            "status.</b> Papers with harvested evidence link to their breakdown; the rest are an "
            "honestly-declared coverage gap, not a zero.</p>",
            "<table><thead><tr><th>#</th><th>Paper</th><th>Year</th><th>Venue</th><th>Evidence</th></tr></thead><tbody>"]
    for pid in sorted(papers):
        p = papers[pid]
        ed = p.get("editorial", {})
        scored = pid in metrics_by_work
        title = (f'<a href="work/{esc(pid)}.html">{esc(p["canonical_title"])}</a>'
                 if scored else esc(p["canonical_title"]))
        ev = '<span class="tag">scored</span>' if scored else '<span class="tag miss">no evidence yet</span>'
        rows.append(
            f'<tr><td class="num">{esc(pid.split("-")[-1])}</td><td>{title}</td>'
            f'<td class="num">{esc(p.get("year",""))}</td><td>{esc(ed.get("venue",""))}</td><td>{ev}</td></tr>'
        )
    rows.append("</tbody></table>")
    return shell("papers.html", "Shelf", "Papers", "".join(rows))


def page_method() -> str:
    rules = [
        "Deterministic scoring — identical inputs + weights produce identical ranks; reproducible from the audit package with one command.",
        "Provenance on every number — source, retrieved_at, confidence, licence note. A number without provenance does not exist.",
        "No silent imputation — missing evidence is recorded as missing and penalized by a published rule, never estimated.",
        "Domains never cross-rank — books, papers, reports, and standards are scored within their own domain.",
        "Each language ecosystem scores within itself first — coverage gaps are declared, not hidden.",
        "People are context, not contestants — persons, organizations, and platforms carry no score, ever.",
        "Manual decisions are records — every override carries a written rationale and is published; Apparens-authored works are flagged.",
        "Humility on rank — a rank is a transparent output of declared evidence, weights, and missing-data rules at a release date, not a verdict on intrinsic worth.",
    ]
    scn = _scenarios()
    body = ["<h2>Rules the ranking cannot break</h2><ol>"]
    body += [f"<li>{esc(r)}</li>" for r in rules]
    body.append("</ol>")
    body.append(f'<h2>Ontology v{esc(ONTOLOGY_VERSION)} (frozen)</h2>'
                '<p>Canonical entities (book, paper, report, standard) are scored within their domain. '
                'Context entities (person, organization, platform) are described, never ranked — '
                'structurally, they carry no score field. Governance records (releases, challenges, '
                'overrides) are append-only.</p>')
    body.append("<h2>Weighting scenarios</h2>")
    metric_names = sorted({m for s in scn["scenarios"].values() for m in s["weights"]})
    head = "".join(f"<th>{esc(m)}</th>" for m in metric_names)
    body.append(f"<table><thead><tr><th>Scenario</th>{head}</tr></thead><tbody>")
    for name in sorted(scn["scenarios"]):
        w = scn["scenarios"][name]["weights"]
        cells = "".join(f'<td class="num">{esc(w.get(m,"—"))}</td>' for m in metric_names)
        body.append(f'<tr><td class="mono">{esc(name)}</td>{cells}</tr>')
    body.append("</tbody></table>")
    body.append(f'<p class="note">Missing-data penalty factor: <b>{esc(scn.get("missing_data_penalty_factor"))}</b>. '
                f'Normalization: <b>{esc(scn.get("normalization"))}</b>. method_version <b>{esc(METHOD_VERSION)}</b>. '
                "These are pilot placeholder weights; every change ships with a changelog entry.</p>")
    return shell("method.html", "Method statement", "Method", "".join(body))


def page_challenges() -> str:
    body = (
        '<p class="note">Anyone may challenge any entry, rank, metric, category, or method rule — '
        "including ours. A challenge is contested against the cited evidence, not against opinion.</p>"
        "<h3>Protocol</h3><ol>"
        "<li>Send the target, your claim, and your evidence to <a href=\"mailto:office@apparens.nl\">office@apparens.nl</a>.</li>"
        "<li>Acknowledgement within 7 days; each challenge receives a public identifier.</li>"
        "<li>Resolution against the data: upheld challenges change the next release; rejected challenges are answered with the evidence.</li>"
        "<li>All challenges and resolutions remain visible permanently.</li></ol>"
        "<h2>Challenge log</h2>"
        '<p class="mono miss">No challenges resolved yet. This log is append-only and will record every one.</p>'
    )
    return shell("challenges.html", "Challenge protocol", "Challenges", body)


def page_changelog() -> str:
    md = (_ROOT / "CHANGELOG.md").read_text("utf-8")
    out, in_list = [], False
    for line in md.splitlines():
        if line.startswith("### "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h3>{esc(line[4:])}</h3>")
        elif line.startswith("## "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h2>{esc(line[3:])}</h2>")
        elif line.startswith("# "):
            continue
        elif line.strip().startswith("- "):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{esc(line.strip()[2:])}</li>")
        elif line.strip():
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<p>{esc(line)}</p>")
    if in_list:
        out.append("</ul>")
    return shell("changelog.html", "Append-only", "Changelog", "".join(out))


def page_data(release: dict, coverage: dict) -> str:
    body = [
        '<p class="note">The proof ships with the claim. Every release is downloadable as an audit '
        "package: the corpus snapshot, the weights, the per-work breakdowns, and the one command that "
        "reproduces the ranking. If you cannot rebuild the rank from the package, the release is defective.</p>",
        "<h2>This release</h2>",
        f'<p class="mono">version <b>{esc(release["version"])}</b> · corpus_hash <b>{esc(release["corpus_hash"][:24])}…</b> · '
        f'method_version {esc(release["method_version"])}</p>',
        f'<p>Metrics: <b>{esc(coverage.get("metrics_total"))}</b> '
        f'({", ".join(f"{esc(k)}: {esc(v)}" for k,v in coverage.get("by_metric_name",{}).items())}); '
        f'declared gaps: {esc(coverage.get("openalex_gaps"))}.</p>',
        "<h2>Downloads</h2><ul>"
        f'<li><a href="audit/{esc(VERSION)}/release.json">release.json</a> — the governance record</li>'
        f'<li><a href="audit/{esc(VERSION)}/coverage.json">coverage.json</a> — declared gaps</li>'
        f'<li><a href="audit/{esc(VERSION)}/rankings/">rankings/</a> — Top-50 per scenario</li>'
        f'<li><a href="audit/{esc(VERSION)}/breakdowns/">breakdowns/</a> — per-work evidence</li>'
        '<li><a href="audit/seeds/papers.json">papers.json</a> — the paper corpus (open JSON)</li>'
        "</ul>",
        "<h2>Reproduce</h2>"
        '<p class="mono">make install &amp;&amp; make assemble &amp;&amp; make release &amp;&amp; make verify-release</p>'
        "<p>The last command rebuilds this release from the pinned inputs and asserts the corpus_hash "
        "and rankings are bit-identical. A mismatch means the release is defective — and we want the challenge.</p>",
    ]
    return shell("data.html", "Data & audit", "Data & audit", "".join(body))


_TEASER_MARKER = "<!--CANON50_TEASER_ROWS-->"


def inject_home_teaser(rankings: dict, papers: dict) -> bool:
    """Fill the homepage Canon-50 teaser with the LIVE top-3 (academic), so the
    approved manifesto never carries hand-typed ranking data that can drift."""
    index = SITE / "index.html"
    if not index.exists():
        return False
    src = index.read_text("utf-8")
    if _TEASER_MARKER not in src:
        return False
    rows = rankings.get("paper__academic", [])[:3]
    out = []
    for r in rows:
        title = esc(papers.get(r["work_id"], {}).get("canonical_title", r["work_id"]))
        out.append(
            f'<tr><td class="rank" style="color:var(--navy-soft)">{r["rank"]:03d}</td>'
            f'<td style="color:var(--navy)"><a href="work/{esc(r["work_id"])}.html">{title}</a></td>'
            f'<td style="color:var(--navy-soft)">paper</td>'
            f'<td style="color:var(--navy-soft)">{r["score"]:.4f}</td>'
            f'<td style="color:var(--navy-soft)">citations, recency</td></tr>'
        )
    # Keep the marker so the injection is idempotent across rebuilds.
    block = _TEASER_MARKER + "\n          " + "\n          ".join(out)
    import re

    src = re.sub(re.escape(_TEASER_MARKER) + r"(?:\s*<tr>.*?</tr>)*", block, src, count=1, flags=re.S)
    index.write_text(src, encoding="utf-8")
    return True


def build() -> dict:
    release = _load(RELEASES / VERSION / "release.json")
    rankings = {
        p.stem: _load(p) for p in sorted((RELEASES / VERSION / "rankings").glob("*.json"))
    }
    breakdowns = {
        p.stem: _load(p) for p in sorted((RELEASES / VERSION / "breakdowns").glob("*.json"))
    }
    papers = _papers_index()
    scored = set(breakdowns)

    _write("canon-50.html", page_canon50(release, rankings, papers))
    for wid, per_scenario in breakdowns.items():
        _write(f"work/{wid}.html", page_work(wid, per_scenario, papers))
    _write("papers.html", page_papers(papers, scored))
    _write("method.html", page_method())
    _write("challenges.html", page_challenges())
    _write("changelog.html", page_changelog())

    coverage = _load(RELEASES / VERSION / "coverage.json")
    _write("data.html", page_data(release, coverage))

    teaser_ok = inject_home_teaser(rankings, papers)

    # Copy the audit package + open corpus so they are publicly downloadable.
    audit_rel = SITE / "audit" / VERSION
    if audit_rel.exists():
        shutil.rmtree(audit_rel)
    shutil.copytree(RELEASES / VERSION, audit_rel)
    (SITE / "audit" / "seeds").mkdir(parents=True, exist_ok=True)
    shutil.copy(SEEDS / "papers.json", SITE / "audit" / "seeds" / "papers.json")

    summary = {"pages": 6 + len(breakdowns), "work_pages": len(breakdowns),
               "home_teaser_injected": teaser_ok, "version": VERSION}
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build()
