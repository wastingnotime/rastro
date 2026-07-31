# Refinement check: first slice

## Evidence

- Unit tests cover mileage-only, date-only, combined, missing baseline,
  disabled, overdue, and next-action behavior.
- The runtime adapter emits semantic status and next-action observations.
- Service completion now emits an explicit domain event and resets only the
  completed item's baseline.

## Current conclusion

The first hypothesis is executable for a single motorcycle and deterministic
maintenance items. The model correctly avoids treating missing mileage
baselines as healthy. The service refinement confirms that a partial service
does not reset unrelated maintenance items.

## Questions carried forward

- Model stale odometer readings rather than assuming the latest reading is
  current.
- Decide how multiple simultaneous due items are grouped for the owner.
