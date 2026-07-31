# Validation receipt: mixed-urgency-groups-build

Date: 2026-07-31

Result: 36 unit tests passed. The grouped attention projection preserves
`overdue`, `due`, and `approaching_due` groups in that order, while
`next_actions()` remains the primary highest-urgency action contract.
