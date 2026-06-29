#!/usr/bin/env bash
# The AI Canon ship gate. Mirrors the app's gate.sh: every [S##] guardrail in
# ARCHITECTURE.md has a check here, and [S12] fails the gate if the two diverge.
# Run: bash scripts/static-gate.sh   (uses .venv if present, else python3)
set -uo pipefail
cd "$(dirname "$0")/.."

PY="${PY:-}"; [ -z "$PY" ] && { [ -x .venv/bin/python ] && PY=.venv/bin/python || PY=python3; }
fail=0
run(){ local label="$1"; shift; printf '── %s\n' "$label"; if "$@" >/tmp/canon_gate.log 2>&1; then echo "   PASS"; else echo "   FAIL"; sed 's/^/   | /' /tmp/canon_gate.log | tail -8; fail=1; fi; }

run "[S0] python syntax"            bash -c "$PY -m py_compile src/canon/*.py src/canon/harvest/*.py"
run "[S1-S10] test suite"           bash -c "PYTHONPATH=src $PY -m pytest -q"
run "[S2] no ad/affiliate/tracker"  bash scripts/guard_no_trackers.sh
run "[S11] clean deployable (no source/secrets in site/)" \
    bash -c '! find site -type f \( -name "*.py" -o -name "*.pyc" -o -name ".env" -o -name "*.sqlite*" \) | grep -q .'
run "[S12] architecture drift"      bash -c '
  for s in S0 S1 S2 S3 S4 S5 S6 S7 S8 S9 S10 S11 S12; do
    grep -q "\[$s\]" ARCHITECTURE.md || { echo "ARCHITECTURE.md missing [$s]"; exit 1; }
  done'

echo
if [ "$fail" = 0 ]; then echo "GATE PASS"; else echo "GATE FAIL"; exit 1; fi
