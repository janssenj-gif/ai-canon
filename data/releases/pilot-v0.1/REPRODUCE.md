# Reproduce pilot-v0.1

This release rebuilds deterministically from the repository.

```bash
make install
make assemble          # derive metrics from the write-once raw cache
make release           # rebuild this release
make verify-release    # assert corpus_hash + rankings are bit-identical
```

- corpus_hash: `bec66b9d32f56559e1ac59656dced24447cf0004ddcac3d36f9ad4fd1e16232f`
- method_version: `0.1-pilot`
- date (metadata, not hashed): 2026-06-29

If `make verify-release` reports MISMATCH, the release is defective — file a challenge
to office@apparens.nl.
