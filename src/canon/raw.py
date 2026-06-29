"""Write-once raw harvest store (CLAUDE.md rule 6).

data/raw/ is the immutable record of what each source returned. Harvesters write
here exactly once per (source, key); a second write with *different* bytes raises
RawImmutableError. Re-writing identical bytes is a no-op so re-runs are safe.

Because the cache is the pinned record, re-running a harvester reads from raw/
and is deterministic — a release can be rebuilt from the audit package without
the network (rule 3). Corrections happen in data/overrides/, never here.

The per-source manifest stores only sha256 + byte length (no timestamps), so the
manifest itself is reproducible.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


class RawImmutableError(RuntimeError):
    """Raised on an attempt to overwrite a raw record with different bytes."""


def _as_bytes(content: str | bytes) -> bytes:
    return content.encode("utf-8") if isinstance(content, str) else content


def _manifest_path(source: str) -> Path:
    return RAW_DIR / source / "manifest.json"


def _load_manifest(source: str) -> dict:
    path = _manifest_path(source)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_manifest(source: str, manifest: dict) -> None:
    path = _manifest_path(source)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {k: manifest[k] for k in sorted(manifest)}
    path.write_text(
        json.dumps(ordered, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def raw_path(source: str, name: str) -> Path:
    return RAW_DIR / source / name


def exists(source: str, name: str) -> bool:
    return raw_path(source, name).exists()


def read(source: str, name: str) -> bytes | None:
    path = raw_path(source, name)
    return path.read_bytes() if path.exists() else None


def write_once(source: str, name: str, content: str | bytes) -> Path:
    """Write a raw record once. Identical re-write is a no-op; a differing
    re-write raises RawImmutableError (rule 6)."""
    data = _as_bytes(content)
    digest = hashlib.sha256(data).hexdigest()
    path = raw_path(source, name)

    if path.exists():
        existing = hashlib.sha256(path.read_bytes()).hexdigest()
        if existing != digest:
            raise RawImmutableError(
                f"raw/{source}/{name} already exists with different bytes; "
                "raw/ is write-once — make corrections in data/overrides/"
            )
        return path  # identical: idempotent no-op

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    manifest = _load_manifest(source)
    manifest[name] = {"sha256": digest, "bytes": len(data)}
    _save_manifest(source, manifest)
    return path
