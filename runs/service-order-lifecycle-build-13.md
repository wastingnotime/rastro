# Service order lifecycle build 13

## Verification

- Unit suite: 105 tests passed.

## Built boundary

Event names, actors, and detail keys now reject non-text values as well as
blank values, producing domain errors instead of incidental attribute errors.
