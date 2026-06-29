"""Harvesters and metric assembly (Stage A, Sprint 2).

Harvesters populate the write-once raw cache (data/raw/<source>/). Metrics are
*derived* from that cache at assembly time, so parsing changes never fight raw
immutability and a release rebuilds deterministically from the cached snapshot.
"""
