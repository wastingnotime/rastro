# Refinement check: first slice

## Evidence

- Unit tests cover mileage-only, date-only, combined, missing baseline,
  disabled, overdue, and next-action behavior.
- The runtime adapter emits semantic status and next-action observations.
- Service completion now emits an explicit domain event and resets only the
  completed item's baseline.
- Odometer freshness is now modeled explicitly; readings older than 90 days
  produce `unknown` for mileage-driven status.
- Equally urgent items are grouped in deterministic title order to reduce
  reminder noise while retaining item-level detail.
- Date-based document obligations now join the combined owner attention
  projection without being folded into mechanical maintenance rules.
- One-year profile evidence confirms active riders remain fresh while a
  long-unused motorcycle becomes unknown after 90 days.
- Reminder cadence evidence suppresses next-day repeats while preserving
  immediate first reminders and escalation behavior.
- Partial service records now update selected item baselines and retain
  provider/note evidence without changing unselected items.
- Service correction projection now restores the prior active baseline after a
  later record is voided, without deleting history.
- The service-history application boundary now denies non-owner corrections and
  reports explicit errors for unknown or already-voided records.
- Correction failures now have stable codes and safe user-facing messages,
  with runtime evidence for the forbidden case.
- The application adapter now returns a stable correction response envelope and
  leaves state unchanged when a command is rejected.
- Same-day due items are now explicitly grouped and covered by a runtime
  invariant.
- Mixed urgency groups now preserve priority order and lower-priority context
  without changing the primary action helper.
- The attention presentation expands the primary group and collapses lower
  groups by default; the runtime trace now demonstrates both states.
- One-year cadence comparison shows 14 days as a practical exploratory
  midpoint: commuter 19 reminders and weekend rider 17 reminders.

## Current conclusion

The first hypothesis is executable for a single motorcycle and deterministic
maintenance items. The model correctly avoids treating missing mileage
baselines as healthy. The service refinement confirms that a partial service
does not reset unrelated maintenance items.

## Questions carried forward

- Evaluate reminder noise over longer commuter and weekend-rider scenarios.
- Decide whether persistent overdue states need cadence, suppression, or
  service-completion prompts in the owner experience.
- Tune the 14-day default against observed owner return behavior.
- Validate cadence with real pilot return behavior before treating 14 days as a
  product default.
- Revisit correction copy with pilot users and localize only after the contract
  is validated.
- Decide how mixed-urgency groups should be presented in the owner interface.
- Validate whether lower-priority groups should collapse by default in pilot
  usability sessions.
- Decide whether expand/collapse choices should persist between visits.
