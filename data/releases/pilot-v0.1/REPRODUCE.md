# Reproduce pilot-v0.1

This release rebuilds deterministically from the repository.

```bash
make install
make assemble          # derive metrics from the write-once raw cache
make release           # rebuild this release
make verify-release    # assert corpus_hash + rankings are bit-identical
```

- corpus_hash: `b8e76cc87afcb2a51cb7dfef005784c941bfdcf9769bfd1470f2df2d38de72c2`
- method_version: `0.1-pilot`
- date (metadata, not hashed): 2026-06-29

If `make verify-release` reports MISMATCH, the release is defective — file a challenge
to office@apparens.nl.
