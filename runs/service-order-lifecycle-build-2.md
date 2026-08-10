# Service order lifecycle build 2

## Verification

- Unit suite: 97 tests passed.
- Runtime validator: 161 observations and 21 owner-start executions validated.

## Built boundary

Invoice and payment domain events retain the accepted proposal version. The
payment event also retains its reference, allowing financial evidence to be
traced back to the negotiated agreement.
