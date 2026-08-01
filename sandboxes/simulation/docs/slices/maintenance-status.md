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

Reminder cadence is now explicit: actionable items remind immediately when
first observed, repeat after 14 days by default, and remind immediately when
their status escalates. `ok` and `unknown` states do not produce reminders.

The current profile comparison keeps 14 days as an exploratory midpoint: it
produces 19 commuter reminders and 17 weekend-rider reminders in one year,
compared with 37/31 at 7 days and 9/9 at 30 days.

Service records now support partial completion. A single `ServiceRecorded`
event updates only the selected item baselines, preserving the remaining
items' history and status.

Corrections are append-only: `ServiceRecordVoided` marks an incorrect record
inactive, and the projection selects the latest remaining active record for
each maintenance item. The original record and void reason remain auditable.

The application boundary binds correction commands to `owner_id`. Unauthorized
actors, unknown records, and repeated voids receive explicit errors before a
domain event is appended.

Correction errors expose stable codes and safe messages for application
adapters. The runtime scenario emits the forbidden correction contract for a
non-owner actor.

`CorrectionCommand` and `CorrectionResponse` provide a framework-neutral
adapter boundary. Rejected commands return `accepted: false` and preserve the
original state.

Same-day due items are confirmed to share one grouped owner action, sorted by
title and retaining item-level detail.

Mixed urgency is represented as ordered `AttentionGroup` values: overdue,
then due, then approaching due. `next_actions()` continues to expose only the
first group for the primary action, while the grouped view preserves context.

The presentation contract expands the first group and collapses lower-priority
groups by default. An explicit `expand_all` option supports inspection without
changing the underlying attention ordering.

`AttentionViewPreferences` can persist selected urgency expansions between
visits. The preference changes presentation only; it never changes status,
priority, or reminder behavior. Preferences are scoped per motorcycle to avoid
cross-vehicle layout leakage.

Cross-device synchronization uses revisioned snapshots. Snapshots must share a
motorcycle and owner scope; the highest revision wins, and equal revisions use
device ID as a deterministic tie-breaker.

`AttentionSyncState` and `AttentionSyncResponse` define the owner-authorized
storage boundary without selecting a database or authentication framework.
Accepted writes return `preference_sync_accepted`; unauthorized writes are
rejected without mutating stored snapshots.

The `AttentionPreferenceStore` port and in-memory fake demonstrate the storage
contract: snapshots are isolated by `(owner_id, motorcycle_id)` and retain the
revision winner across writes. Blank motorcycle scopes are rejected at snapshot
creation.

`OwnerStatusView` is the first owner-facing query contract. It combines
maintenance and document assessments, retains their source labels, preserves
odometer metadata, and returns the highest-urgency action titles.
Callers can configure the odometer freshness threshold; the default remains 90
days.

`owner_status_payload` serializes this query into a snake_case JSON-ready
contract, preserving null odometer dates and per-item source/status fields.
The payload currently declares `schema_version: 1`; material changes must
increment that version.

The API adapter contract is `/api/v1/motorcycles/{motorcycle_id}/maintenance-status`.
Owner requests return the versioned payload; non-owner requests return 403
without status data.

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
- reminder cadence suppresses same-status daily repeats and preserves escalation;
- partial service records reset only selected maintenance items;
- voiding an incorrect later record restores the prior active baseline;
- only the motorcycle owner can void a service record;
- correction failures expose stable adapter-facing codes and messages;
- rejected correction commands do not mutate service-history state;
- same-day due items are grouped into one owner action;
- mixed urgency groups preserve priority and lower-priority context;
- primary attention expands while lower-priority groups collapse by default;
- selected lower-priority expansions can persist between visits;
- preference state does not leak between motorcycles;
- same-motorcycle preference snapshots merge deterministically across devices;
- cross-owner preference snapshots are rejected;
- only the authenticated owner can write preference snapshots;
- account storage isolates owner and motorcycle preference scopes;
- blank motorcycle scopes cannot enter sync or storage;
- owner status combines maintenance and document attention deterministically;
- owner status exposes configurable odometer freshness;
- owner status payload preserves uncertainty and source labels;
- owner status payload declares an explicit schema version;
- owner status API enforces private-by-default access;
- invariant confirms unknown data never becomes healthy.

## Out of scope

Service recording, document obligations, authentication, sharing, persistence,
browser behavior, and mechanical diagnosis.
