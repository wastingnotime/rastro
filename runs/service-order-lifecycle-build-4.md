# Service order lifecycle build 4

## Verification

- Unit suite: 99 tests passed.
- Runtime validator: 161 observations and 21 owner-start executions validated.

## Built boundary

Owner responses can include the proposal version they reviewed. Mismatched
versions are rejected without changing the order, preventing stale clients
from accepting an obsolete proposal.
