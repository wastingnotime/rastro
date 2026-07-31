# Slice: deterministic maintenance status

## Selected implementation pack

Python event-oriented simulation with a repository-owned adapter to the WNT MRL
Runtime.

## Use-case contract

Given a current motorcycle odometer/date and an item's last service baseline,
calculate status and emit the most urgent next maintenance action.

## Rules

- mileage and date intervals are optional independently;
- when both exist, the earliest due dimension controls the status;
- warning thresholds apply before due;
- missing required data produces `unknown`;
- disabled items produce no action;
- status calculation is deterministic and timezone-aware.

## Scenario

Start a daily-commuter motorcycle at 18,420 km on 2026-07-31 with engine oil
well within its interval and chain inspection 120 km from its warning
threshold. Advance to a later reading where the chain becomes due and emit the
next action.

## Refinement: service completion baseline reset

Service completion is represented as an explicit `ServiceCompleted` domain
event. Applying it to one maintenance item resets that item's date and mileage
baseline while leaving the other items unchanged.

The mileage freshness policy is explicit: an odometer reading older than 90
days is stale by default and produces `unknown` for mileage-driven status. The
threshold is configurable for scenario exploration.

Grouped attention is now explicit: all items tied at the highest urgency are
returned in stable title order. Less urgent items remain available to the
status view but do not add another immediate reminder group.

Document obligations use the same status vocabulary but remain a separate
date-based model. The combined owner projection merges their actionable
assessments with maintenance assessments at the highest urgency.

One-year profile refinement compares daily commuter, weekend rider, and
long-unused ownership patterns. Active profiles retain fresh mileage status;
the long-unused profile becomes `unknown` after the 90-day freshness window.

## Done criteria

- mileage-only, date-only, combined, missing-data, disabled, and overdue cases
  have deterministic tests;
- runtime adapter emits status and next-action observations;
- service completion emits an auditable event and recalculates the completed
  item from its new baseline;
- stale odometer readings produce `unknown` for mileage-driven items;
- equally urgent maintenance items are grouped into one attention observation;
- completed or disabled document obligations do not create owner attention;
- document and maintenance actions can appear together in owner attention;
- one-year ownership profiles produce deterministic freshness evidence;
- invariant confirms unknown data never becomes healthy.

## Out of scope

Service recording, document obligations, authentication, sharing, persistence,
browser behavior, and mechanical diagnosis.
