# Service order lifecycle build 12

## Verification

- Unit suite: 105 tests passed.
- Runtime validator: 161 observations and 21 owner-start executions validated.

## Built boundary

Payments now reject zero or negative amounts explicitly before invoice
comparison, keeping the settlement boundary financially meaningful.
