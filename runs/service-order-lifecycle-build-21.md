# Service order lifecycle build 21

## Verification

- Unit suite: 109 tests passed.

## Built boundary

Cancellation now reports a stable domain validation error for non-text or
blank reasons instead of leaking incidental type errors.
