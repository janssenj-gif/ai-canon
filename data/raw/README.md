# data/raw/ — write-once harvest store (rule 6)

Everything here is the immutable record of what a source returned. Harvesters and
operators write once per `(source, key)`; a differing overwrite raises
`RawImmutableError`. Corrections go to `data/overrides/`, never here. Metrics are
*derived* from this store by `canon.harvest.assemble`, so re-deriving never
mutates the record and a release rebuilds from the pinned snapshot.

## Subdirectories

- `openalex/` — cached OpenAlex API responses, one JSON per paper id
  (`paper-0001.json`), plus a `manifest.json` of sha256 + byte length. Populated
  by `make harvest`. CC0 metadata.

## Manual CSV drops (CAN-10)

For sources without a free API (e.g. WorldCat holdings, Open Syllabus
adoptions), drop a CSV into `data/raw/<source>/`. **Every row is a metric and
must carry its own provenance** — there is no way to add an unsourced number.

Exact header required:

```
work_id,metric_name,value,source,retrieved_at,confidence,provenance_url,license_note
```

Example (`data/raw/open_syllabus/adoptions.csv`):

```
work_id,metric_name,value,source,retrieved_at,confidence,provenance_url,license_note
paper-0001,syllabus_adoptions,42,Open Syllabus,2026-06-29,medium,https://opensyllabus.org/result/...,derived counts
```

`confidence` must be one of `low|medium|high`. `value` must be numeric.
Drops are validated against `schema.Metric` at assembly; a bad row fails loudly.
