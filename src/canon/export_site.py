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

_STYLE = """
:root{--navy:#0E2A4A;--navy-soft:#3B5268;--cream:#F4EEE2;--panel:#FBF8F1;
--orange:#E87722;--hairline:#D9CFBE;--mono-bg:#0E2A4A;--mono-ink:#EDE6D6}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--cream);color:var(--navy);font-family:"DM Sans",system-ui,sans-serif;
font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.measure{max-width:980px;margin:0 auto;padding:0 24px}
a{color:var(--navy);text-decoration:underline;text-decoration-color:var(--orange);text-underline-offset:3px}
a:hover{color:var(--orange)}
:focus-visible{outline:3px solid var(--orange);outline-offset:2px}
nav.top{background:var(--navy);color:var(--mono-ink);font-family:"DM Mono",monospace;font-size:13px}
nav.top .measure{display:flex;flex-wrap:wrap;gap:6px 22px;padding:12px 24px}
nav.top a{color:var(--mono-ink);text-decoration:none}
nav.top a:hover,nav.top a[aria-current=page]{color:#fff;border-bottom:2px solid var(--orange)}
header.h{padding:46px 0 22px;border-bottom:1px solid var(--hairline)}
.kicker{font-family:"DM Mono",monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--navy-soft)}
h1{font-family:"DM Serif Display",serif;font-weight:400;font-size:clamp(32px,5vw,52px);line-height:1.05;margin:10px 0}
h2{font-family:"DM Serif Display",serif;font-weight:400;font-size:26px;margin:34px 0 12px}
h3{font-family:"DM Mono",monospace;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--navy-soft);margin:22px 0 8px}
p{margin:10px 0}main{padding:24px 0 60px}
.note{background:var(--panel);border:1px solid var(--hairline);border-left:5px solid var(--orange);padding:14px 18px;margin:18px 0;font-size:14.5px}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14.5px}
th{text-align:left;font-family:"DM Mono",monospace;font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;
color:var(--navy-soft);border-bottom:1px solid var(--navy);padding:8px 10px}
td{padding:8px 10px;border-bottom:1px dashed var(--hairline);vertical-align:top}
td.rank,td.num{font-family:"DM Mono",monospace;white-space:nowrap}
.tag{font-family:"DM Mono",monospace;font-size:11px;padding:1px 7px;border:1px solid var(--hairline);border-radius:10px;color:var(--navy-soft)}
.flag{color:var(--orange);font-weight:600}
.scn{margin:30px 0;border:1px solid var(--hairline);background:var(--panel);padding:18px 20px}
footer{background:var(--navy);color:#8FA3B8;font-family:"DM Mono",monospace;font-size:12px;padding:34px 0}
footer a{color:var(--mono-ink)}
.miss{color:var(--navy-soft)}
.mono{font-family:"DM Mono",monospace;font-size:13px}
"""


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def _nav(active: str, prefix: str) -> str:
    items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == active else ""
        items.append(f'<a href="{prefix}{href}"{cur}>{esc(label)}</a>')
    return f'<nav class="top"><div class="measure">{"".join(items)}</div></nav>'


def shell(active: str, kicker: str, title: str, body: str, *, depth: int = 0) -> str:
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} — The AI Canon</title>
<meta name="description" content="The AI Canon — a free, method-backed reference library for AI knowledge.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{_STYLE}</style></head><body>
{_nav(active, prefix)}
<header class="h"><div class="measure"><span class="kicker">{esc(kicker)}</span><h1>{esc(title)}</h1></div></header>
<main><div class="measure">{body}</div></main>
<footer><div class="measure">THE AI CANON · an <a href="https://apparens.nl">Apparens</a> public research initiative ·
release <b>{esc(VERSION)}</b> · challenge anything: <a href="mailto:office@apparens.nl">office@apparens.nl</a><br>
Nothing is for sale. Nothing is hidden. Nothing is final.</div></footer>
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
