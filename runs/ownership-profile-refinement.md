# Validation receipt: ownership-profile-refinement

Date: 2026-07-31

Result: 19 unit tests passed and the runtime profile evidence completed.

| Profile | Unknown days | Attention days |
| --- | ---: | ---: |
| Daily commuter | 0 | 249 |
| Weekend rider | 0 | 215 |
| Long unused | 274 | 0 |

The `long_unused_profile_becomes_unknown` invariant passed. The persistent
overdue counts are now an explicit follow-up question rather than a hidden
assumption about reminder behavior.
