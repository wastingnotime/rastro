# Validation receipt: grouped-maintenance-actions

Date: 2026-07-31

Result: 13 unit tests passed. The grouped action projection returns all items
at the highest urgency in stable title order and preserves `next_action` as a
compatibility helper returning the first grouped item.

Runtime observation:

```text
next_actions_grouped: ["Brake inspection", "Chain inspection"]
```
