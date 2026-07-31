# Validation receipt: reminder-cadence-refinement

Date: 2026-07-31

Result: 24 unit tests passed. One-year reminder counts:

| Profile | 7 days | 14 days | 30 days |
| --- | ---: | ---: | ---: |
| Daily commuter | 37 | 19 | 9 |
| Weekend rider | 31 | 17 | 9 |
| Long unused | 0 | 0 | 0 |

Decision: retain 14 days as the current simulation hypothesis, pending local
pilot evidence about owner return behavior.
