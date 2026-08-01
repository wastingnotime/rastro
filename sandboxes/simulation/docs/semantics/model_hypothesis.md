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
- `AttentionGroup`: one urgency tier and its sorted item assessments; grouped
  views preserve lower-priority context without changing the primary action.
- `AttentionGroupView`: adapter-facing presentation with item titles and an
  explicit expanded/collapsed state.
- `AttentionViewPreferences`: persisted set of urgency groups the owner chose
  to expand, scoped to one motorcycle.
- `AttentionPreferenceSnapshot`: revisioned, device-tagged preference state
  used for deterministic cross-device synchronization and bound to an owner.
- `AttentionSyncState` / `AttentionSyncResponse`: owner-authorized storage
  boundary and framework-neutral synchronization result.
- `AttentionPreferenceStore`: storage port with an owner-scoped in-memory fake
  for deterministic simulation.
- `DocumentObligation`: a date-based licensing, insurance, inspection, or
  warranty obligation with completion state.
- `ReminderTracker`: stateful policy that suppresses same-status repeats,
  repeats after a configured cadence, and reminds immediately on escalation.
- `ServiceRecorded`: auditable service visit event containing the selected
  maintenance items and new service baseline.
- `ServiceRecordVoided`: append-only correction event that removes a record
  from the active projection without deleting history.
- `ServiceHistoryState`: owner-bound application state for service records and
  correction events.
- `ServiceCorrectionError`: stable adapter-facing code and safe user message
  for forbidden, missing, or repeated corrections.
- `CorrectionCommand` / `CorrectionResponse`: framework-neutral command and
  response contract for future API or web adapters.

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
12. Voiding an incorrect later service record should restore the prior active
    baseline deterministically.
13. Only the motorcycle owner may void a service record.
14. Correction failures should expose stable codes and safe messages without
    leaking internal ownership or storage details.
15. Rejected correction commands must not mutate service-history state.
16. Same-motorcycle preference snapshots sync by highest revision, with a
    stable device-ID tie-breaker.
17. Preference snapshots from different owners must never merge, even when
    motorcycle scope IDs collide.
18. Only the authenticated owner may write synchronized preference state.
19. Account storage must isolate owner and motorcycle scopes while preserving
    revision conflict behavior.

## Open questions

- The production storage technology remains a technology-project decision;
  simulation uses the owner-scoped store port and fake provider.

## Candidate next slices

- service completion and interval baseline reset;
- stale odometer and correction history;
- reminder-noise evaluation across grouped due items.
- service cadence and overdue persistence across ownership profiles.
- reminder cadence tuning with real owner return behavior.
- service-record correction history and user-facing error contracts are now
  modeled.
