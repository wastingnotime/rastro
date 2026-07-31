# Model hypothesis

## Boundary

The first simulation boundary is one motorcycle owner, one current odometer
reading, and a set of maintenance items with optional mileage and date
intervals. The model produces deterministic item status and one prioritized
next action.

## Vocabulary

- `MotorcycleState`: current odometer and the simulated current date.
- `MaintenanceItem`: interval configuration and the last completed baseline.
- `MaintenanceStatus`: `ok`, `approaching_due`, `due`, `overdue`, or `unknown`.
- `MaintenanceAssessment`: status plus remaining mileage and days.

## Hypotheses to test

1. Whichever configured dimension becomes due first controls combined status.
2. A warning threshold should produce `approaching_due` before due.
3. Missing current or baseline data should produce `unknown`.
4. The next action should be the most urgent actionable maintenance item.

## Open questions

- How stale may an odometer reading be before mileage status becomes unknown?
- Should same-day due items be grouped into one owner action?
- How should partial service completion affect action grouping?

## Candidate next slices

- service completion and interval baseline reset;
- stale odometer and correction history;
- document obligations and combined owner status;
- multiple due items and reminder-noise evaluation.
