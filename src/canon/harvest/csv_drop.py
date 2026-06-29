"""CAN-10 — manual CSV-drop importer (WorldCat, Open Syllabus, ...).

For sources without a free API (or where a one-off export is simpler for the
pilot), an operator drops a CSV into data/raw/<source>/. Each row IS a metric and
must carry its own provenance (rule 2) — there is no way to add an unsourced
number through this path. Rows are validated against schema.Metric at assembly.

Required header (exact):
    work_id,metric_name,value,source,retrieved_at,confidence,provenance_url,license_note
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

REQUIRED_COLUMNS = [
    "work_id",
    "metric_name",
    "value",
    "source",
    "retrieved_at",
    "confidence",
    "provenance_url",
    "license_note",
]


class CsvDropError(ValueError):
    pass


def parse_csv_text(text: str, *, origin: str = "<text>") -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return []
    missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
    if missing:
        raise CsvDropError(f"{origin}: CSV missing required columns: {missing}")

    rows: list[dict] = []
    for i, row in enumerate(reader, start=2):  # row 1 is the header
        try:
            value = float(str(row["value"]).strip())
        except (TypeError, ValueError) as exc:
            raise CsvDropError(f"{origin} line {i}: value is not numeric: {row.get('value')!r}") from exc
        rows.append(
            {
                "work_id": str(row["work_id"]).strip(),
                "metric_name": str(row["metric_name"]).strip(),
                "value": value,
                "source": str(row["source"]).strip(),
                "retrieved_at": str(row["retrieved_at"]).strip(),
                "confidence": str(row["confidence"]).strip(),
                "provenance_url": str(row["provenance_url"]).strip(),
                "license_note": str(row["license_note"]).strip(),
            }
        )
    return rows


def load_drops(raw_dir: Path) -> list[dict]:
    """Read every *.csv under data/raw/<source>/ (any source) into metric dicts."""
    metrics: list[dict] = []
    if not raw_dir.exists():
        return metrics
    for csv_path in sorted(raw_dir.glob("*/*.csv")):
        metrics.extend(
            parse_csv_text(csv_path.read_text(encoding="utf-8"), origin=str(csv_path))
        )
    return metrics
