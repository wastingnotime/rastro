# Model hypothesis

## Boundary

The first simulation boundary is one motorcycle owner, one current odometer
reading, and a set of maintenance items with optional mileage and date
intervals. The model produces deterministic item status and one prioritized
next action.

## Vocabulary

- `MotorcycleState`: current odometer, simulated current date, and optional
  odometer observation date.
- `MaintenanceItem`: interval configuration and the last completed baseline.
- `MaintenanceStatus`: `ok`, `approaching_due`, `due`, `overdue`, or `unknown`.
- `MaintenanceAssessment`: status plus remaining mileage and days.
- `next_actions`: all maintenance items tied at the highest actionable urgency,
  sorted deterministically for grouped owner attention.
- `DocumentObligation`: a date-based licensing, insurance, inspection, or
  warranty obligation with completion state.
- `ReminderTracker`: stateful policy that suppresses same-status repeats,
  repeats after a configured cadence, and reminds immediately on escalation.

## Hypotheses to test

1. Whichever configured dimension becomes due first controls combined status.
2. A warning threshold should produce `approaching_due` before due.
3. Missing current or baseline data should produce `unknown`.
4. The next action should be the most urgent actionable maintenance item.
5. A mileage status based on an odometer reading older than 90 days should be
   `unknown` by default, with the threshold configurable for exploration.
6. Simultaneous items at the same urgency should be grouped to reduce reminder
   noise while preserving each item title.
7. Mechanical maintenance and document obligations should share owner
   attention without sharing their underlying domain rules.
8. Active commuter and weekend-rider profiles should retain reliable
   mileage-driven status when they record odometer readings regularly.
9. A long-unused motorcycle should transition to `unknown`, not remain `ok`,
   after the freshness window.
10. A 14-day default reminder cadence reduces daily noise without hiding
    escalation.
11. Across the current one-year profiles, 14 days is a reasonable exploratory
    midpoint between 7-day noise and 30-day suppression.

## Open questions

- Should same-day due items be grouped into one owner action?
- How should partial service completion affect action grouping?

## Candidate next slices

- service completion and interval baseline reset;
- stale odometer and correction history;
- reminder-noise evaluation across grouped due items.
- service cadence and overdue persistence across ownership profiles.
- reminder cadence tuning with real owner return behavior.
