# Reminder and ownership-profile refinement

## Change

Strengthened reminder/profile boundaries by validating cadence, profile names,
and simulation duration. Added explicit immediate escalation coverage from
approaching due to due.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`
