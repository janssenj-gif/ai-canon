# The AI Canon — task runner.
#
# We run modules with PYTHONPATH=src rather than an editable install: the
# editable .pth/finder is honored only intermittently when the venv lives under
# ~/Desktop (macOS file-access mediation), whereas PYTHONPATH is deterministic.
# pytest reads `pythonpath = src` from pyproject.toml, so tests need no install.

PY ?= .venv/bin/python
export PYTHONPATH := src

.PHONY: install ingest harvest assemble score score-papers release verify-release redteam site test guard all

install:
	$(PY) -m pip install -q pydantic openpyxl pyyaml pytest

ingest:
	$(PY) -m canon.ingest

harvest:
	$(PY) -m canon.harvest.openalex

assemble:
	$(PY) -m canon.harvest.assemble

score:
	$(PY) -m canon.score --fixtures --scenario academic --work-type book

score-papers:
	$(PY) -m canon.score --corpus --work-type paper --scenario academic --top 20

release:
	$(PY) -m canon.release

verify-release:
	$(PY) -m canon.release --verify

redteam:
	$(PY) -m canon.redteam

site:
	$(PY) -m canon.export_site

test:
	$(PY) -m pytest -q

guard:
	bash scripts/guard_no_trackers.sh

gate:
	bash scripts/static-gate.sh

all: guard test
