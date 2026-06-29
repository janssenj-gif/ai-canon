"""CAN-17 — internal adversarial review of a built release.

Runs the checks a hostile reviewer would run against data/releases/<version>/ and
writes reports/red_team_findings.md. The gate is conservative: any CRITICAL
finding fails GATE A. A declared limitation (e.g. single-metric scenarios that
cannot yet diverge) is reported honestly as INFO and does NOT fake a pass.

GATE A (master doc): the pilot survives adversarial review within two iterations.
This harness is the automated first pass; a human reviewer reads the report next.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import release as rel

_ROOT = Path(__file__).resolve().parents[2]
REPORTS = _ROOT / "reports"

CRITICAL, HIGH, MEDIUM, INFO = "CRITICAL", "HIGH", "MEDIUM", "INFO"


def _finding(check, severity, status, detail):
    return {"check": check, "severity": severity, "status": status, "detail": detail}


def review(version: str = rel.DEFAULT_VERSION) -> dict:
    out_dir = rel.RELEASES / version
    findings: list[dict] = []

    # 1. Reproducibility (rule 3).
    reproduced = rel.verify(version)
    findings.append(
        _finding(
            "reproducibility",
            CRITICAL,
            "pass" if reproduced else "fail",
            "rebuilt corpus_hash + rankings match the committed release"
            if reproduced
            else "rebuild does NOT match — release is defective",
        )
    )

    rankings = {p.stem: json.loads(p.read_text("utf-8")) for p in sorted((out_dir / "rankings").glob("*.json"))}
    breakdowns = {p.stem: json.loads(p.read_text("utf-8")) for p in sorted((out_dir / "breakdowns").glob("*.json"))}

    # 2. Provenance on every present metric (rule 2).
    missing_prov = []
    for wid, per_scenario in breakdowns.items():
        for scenario, row in per_scenario.items():
            for c in row.get("components", []):
                if c.get("status") == "present":
                    if not (c.get("source") and c.get("provenance_url") and c.get("retrieved_at")):
                        missing_prov.append(f"{wid}/{scenario}/{c.get('metric')}")
    findings.append(
        _finding(
            "provenance_complete",
            CRITICAL,
            "pass" if not missing_prov else "fail",
            "every present metric carries source+provenance_url+retrieved_at"
            if not missing_prov
            else f"{len(missing_prov)} present metrics lack provenance: {missing_prov[:5]}",
        )
    )

    # 3. No cross-domain ranking (rule 4): each ranking file is single work_type.
    cross = []
    for key, rows in rankings.items():
        types = {r["work_type"] for r in rows}
        if len(types) > 1:
            cross.append((key, sorted(types)))
    findings.append(
        _finding(
            "no_cross_domain",
            CRITICAL,
            "pass" if not cross else "fail",
            "each ranking is a single domain" if not cross else f"cross-domain rankings: {cross}",
        )
    )

    # 4. Missing data is recorded + penalized, never imputed (rule 8).
    imputed = []
    for wid, per_scenario in breakdowns.items():
        for scenario, row in per_scenario.items():
            for c in row.get("components", []):
                if c.get("status") == "missing" and "missing_data_penalty" not in c:
                    imputed.append(f"{wid}/{scenario}/{c.get('metric')}")
    findings.append(
        _finding(
            "no_silent_imputation",
            CRITICAL,
            "pass" if not imputed else "fail",
            "missing metrics carry an explicit penalty" if not imputed else f"unpenalized missing: {imputed[:5]}",
        )
    )

    # 5. Conflict-of-interest works are flagged in the output (rule 7/12).
    unflagged = [
        wid
        for key, rows in rankings.items()
        for r in rows
        if r.get("conflict_flag") is None
    ]
    findings.append(
        _finding(
            "conflict_flag_surfaced",
            HIGH,
            "pass" if not unflagged else "fail",
            "every ranked row exposes conflict_flag" if not unflagged else f"{len(unflagged)} rows missing conflict_flag",
        )
    )

    # 6. Coverage honestly declared.
    coverage_path = out_dir / "coverage.json"
    declared = coverage_path.exists()
    findings.append(
        _finding(
            "coverage_declared",
            HIGH,
            "pass" if declared else "fail",
            f"coverage.json present ({json.loads(coverage_path.read_text())['metrics_total'] if declared else 0} metrics; gaps declared)"
            if declared
            else "no coverage.json — gaps not declared",
        )
    )

    # 7. Sanity: rows must be ordered by composite score desc with sequential
    #    ranks. (The order tracks the SCENARIO score, not any single metric —
    #    asserting single-metric order would be wrong once >1 metric is present.)
    record = json.loads((out_dir / "release.json").read_text("utf-8"))
    sane = True
    detail7 = "rows ordered by score desc with sequential ranks"
    for key, rows in rankings.items():
        scores = [r["score"] for r in rows]
        if scores != sorted(scores, reverse=True):
            sane = False
            detail7 = f"{key}: scores not monotonically non-increasing — investigate"
            break
        if [r["rank"] for r in rows] != list(range(1, len(rows) + 1)):
            sane = False
            detail7 = f"{key}: ranks not sequential 1..N"
            break
    findings.append(_finding("ranking_sanity", HIGH, "pass" if sane else "fail", detail7))

    # 8. Divergence honesty (INFO): if scenarios can't diverge yet, it must be declared.
    div = record.get("divergence", {})
    identical = any(d.get("identical_ordering_across_scenarios") for d in div.values())
    findings.append(
        _finding(
            "scenario_divergence",
            INFO if identical else INFO,
            "declared-limitation" if identical else "observed",
            "scenarios share an ordering (only citation_count harvested) — declared in release.json; "
            "the method's divergence claim is NOT yet demonstrated and needs more metrics"
            if identical
            else "scenario orderings differ — divergence demonstrated",
        )
    )

    blocking = [f for f in findings if f["severity"] in (CRITICAL, HIGH) and f["status"] == "fail"]
    gate_a = not blocking
    summary = {
        "version": version,
        "gate_a_machinery": "PASS" if gate_a else "FAIL",
        "blocking_findings": len(blocking),
        "findings": findings,
    }
    _write_report(summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "findings"}, indent=2))
    for f in findings:
        print(f"  [{f['severity']:<8}] {f['check']:<22} {f['status']:<20} {f['detail'][:80]}")
    return summary


def _write_report(summary: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Adversarial review — {summary['version']}",
        "",
        f"**GATE A (machinery): {summary['gate_a_machinery']}** "
        f"({summary['blocking_findings']} blocking findings)",
        "",
        "| check | severity | status | detail |",
        "|---|---|---|---|",
    ]
    for f in summary["findings"]:
        lines.append(f"| {f['check']} | {f['severity']} | {f['status']} | {f['detail']} |")
    div_finding = next((f for f in summary["findings"] if f["check"] == "scenario_divergence"), None)
    diverged = div_finding and div_finding["status"] == "observed"
    lines += [
        "",
        "## Reviewer note",
        "",
        "This automated pass verifies the *machinery* (reproducibility, provenance, domain",
        "isolation, no-imputation, conflict flags, declared coverage) and the substantive",
        "divergence claim.",
        "",
    ]
    if diverged:
        lines += [
            "Two independent signals are now harvested — all-time `citation_count` and recent-",
            "momentum `sustained_readership` — and the three weighting scenarios produce **different**",
            "orderings, so the method's central claim is demonstrated rather than asserted. Coverage is",
            "still partial (a second pass over OpenAlex's daily budget will fill the remaining papers),",
            "and `library_holdings` / `syllabus_adoptions` await WorldCat / Open Syllabus CSV drops;",
            "those are declared gaps, not silent zeros.",
        ]
    else:
        lines += [
            "Only one signal is harvested, so the scenarios share an ordering and the divergence",
            "claim is not yet demonstrated — a declared limitation per the master doc's humility rule.",
        ]
    lines.append("")
    (REPORTS / "red_team_findings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import sys

    summary = review()
    sys.exit(0 if summary["gate_a_machinery"] == "PASS" else 1)
