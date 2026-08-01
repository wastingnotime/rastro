# Owner status and obligation refinement

## Change

Strengthened document-obligation and owner-status boundaries. Obligation titles
and warning windows are validated, while owner-status construction validates
motorcycle scope and odometer freshness configuration.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`
