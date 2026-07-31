# Validation receipt: attention-preference-sync-build

Date: 2026-07-31

Result: 42 unit tests passed. Same-motorcycle preference snapshots merge by
revision, with device ID as a deterministic tie-breaker. Cross-motorcycle
merges are rejected. Runtime selected the `web` revision 3 snapshot over the
`phone` revision 2 snapshot.
