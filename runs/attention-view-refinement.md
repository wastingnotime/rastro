# Validation receipt: attention-view-refinement

Date: 2026-07-31

Result: 37 unit tests passed. The runtime attention view contains:

```text
overdue: ["Tire inspection"] expanded=true
approaching_due: ["Brake inspection", "Chain inspection"] expanded=false
```

The first urgency group is visible immediately; lower-priority context remains
available without competing with the primary action.
