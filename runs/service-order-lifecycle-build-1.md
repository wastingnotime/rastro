# Service order lifecycle build 1

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- Result: 97 tests passed.

## Built boundary

Service requests and proposals now reject blank maintenance-gap and part
evidence before it enters the lifecycle model.
