# Maintenance threshold history build

## Change

Added `project_warning_threshold_history` to replay owner customization and
manufacturer restoration events into an effective maintenance item.

The projection preserves the manufacturer baseline, validates event ordering,
rejects events for another maintenance item, and rejects unknown dimensions.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`
