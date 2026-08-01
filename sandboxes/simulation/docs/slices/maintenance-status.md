# Slice: deterministic maintenance status

## Selected implementation pack

Python event-oriented simulation with a repository-owned adapter to the WNT MRL
Runtime.

## Use-case contract

Given a current motorcycle odometer/date and an item's last service baseline,
calculate status and emit the most urgent next maintenance action.

The application surface now names the user-facing interactions explicitly:
`ViewOwnerStatus`, `RecordService`, `CorrectServiceRecord`,
`CustomizeWarningThresholds`, `SyncAttentionPreferences`, and
`RecordOdometerReading`. These use cases
translate commands and queries into the existing domain functions while
keeping adapters framework-neutral.

## Rules

- mileage and date intervals are optional independently;
- when both exist, the earliest due dimension controls the status;
- warning thresholds apply before due;
- effective warning thresholds retain manufacturer/owner provenance;
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
Document obligation titles and warning windows are validated, and owner-status
construction rejects blank motorcycle scopes or negative freshness windows.

One-year profile refinement compares daily commuter, weekend rider, and
long-unused ownership patterns. Active profiles retain fresh mileage status;
the long-unused profile becomes `unknown` after the 90-day freshness window.

Reminder cadence is now explicit: actionable items remind immediately when
first observed, repeat after 14 days by default, and remind immediately when
their status escalates. `ok` and `unknown` states do not produce reminders.

The current profile comparison keeps 14 days as an exploratory midpoint: it
produces 19 commuter reminders and 17 weekend-rider reminders in one year,
compared with 37/31 at 7 days and 9/9 at 30 days.
Reminder cadence, profile identity, and simulation duration are validated at
their boundaries. Escalation is tested for both approaching-to-due and
approaching-to-overdue transitions.

Service records now support partial completion. A single `ServiceRecorded`
event updates only the selected item baselines, preserving the remaining
items' history and status.

Corrections are append-only: `ServiceRecordVoided` marks an incorrect record
inactive, and the projection selects the latest remaining active record for
each maintenance item. The original record and void reason remain auditable.

The application boundary binds correction commands to `owner_id`. Unauthorized
actors, unknown records, and repeated voids receive explicit errors before a
domain event is appended.

The runtime adapter now exercises the named application use cases for owner
status, preference synchronization, service correction, and odometer
correction, keeping runtime observations representative of the application
boundary.

Each of those executions is also visible as a `use_case_executed` runtime
observation with the use-case name and a consistent `payload.outcome` value;
the payload also classifies the interaction as `query` or `command` while
operation-specific details remain alongside it.

The query/command classification is owned by the application use-case catalog,
so runtime call sites cannot silently disagree about an interaction's kind.
The scenario emits that catalog before the first domain observation, making the
available use cases visible even before one is executed. Each catalog entry
also includes a concise purpose so the simulation explains the interaction
semantics directly. Catalog definitions reject blank names and purposes.
Stable IDs are included in catalog, execution, and summary observations for
machine-readable correlation. Catalog indexing rejects duplicate display names
and duplicate stable IDs before the runtime can publish them.

The service-history query is exercised before and after a voided record: the
active view excludes the voided event while the append-only audit event remains
present in state.

The owner service-history API is exposed at
`/api/v1/motorcycles/{motorcycle_id}/service-history`; it returns the active
history with the shared schema version and rejects non-owner requests without
record data. The runtime scenario emits both the successful owner response and
the forbidden non-owner response.

The observatory graph also exposes every application use case as a first-class
`use_case` node connected from the motorcycle owner, with query/command realm
labels and purpose descriptions. Runtime observations are not the only way to
discover the use-case surface.
Threshold customization, restoration, service recording, and service voiding
are also declared as domain-event nodes with use-case emission edges, allowing
their runtime event beams to render as distinct graph paths.

Use-case executions are summarized by runtime phase with counts by kind,
outcome, and executed name. The owner-start flow and the odometer invariant
are separate phases because the runtime evaluates invariants after actor
execution.

The supervised scenario starts paused with the owner flow queued at the
initial simulation time plus a five-second delay. Reset therefore starts with
no domain events; Play or Step advances to the delayed flow before executing
it. The batch semantic runner still drains the queue so it can produce a
complete deterministic receipt.

Warning thresholds now carry `ThresholdSource`: manufacturer defaults remain
unchanged until `customize_warning_thresholds` applies an owner override. The
override is validated for non-negative values and requires at least one
dimension. `MaintenanceAssessment` carries the same provenance through status
calculation, including `unknown` outcomes. Mileage and date thresholds retain
separate provenance; the aggregate is `mixed` when only one dimension is
customized. `WarningThresholdsCustomized` records the before/after values when
an owner preference is applied.

`MaintenanceItem` validates its policy at construction: titles must be
present, and intervals, warning values, and persisted manufacturer baselines
cannot be negative.

`restore_manufacturer_warning_thresholds` provides the reverse transition when
the canonical manufacturer values are known, resetting both warning
provenance dimensions to `manufacturer`. `WarningThresholdsRestored` records
that reset as an audit event. Both audit events expose the dimensions that
actually changed (`mileage`, `date`, or both). The first owner customization
persists the manufacturer baseline on the item, allowing restoration without
repeating canonical values; explicit values remain supported for imported
plans. Manufacturer-sourced items initialize that baseline at construction;
owner-sourced imported policies may remain without a canonical baseline until
one is supplied. A manufacturer-sourced effective value must always match its
persisted baseline.

`project_warning_threshold_history` replays those audit events into an
effective maintenance policy. It verifies item identity and each event's
previous values, so a missing or misordered threshold event fails explicitly
instead of silently producing an incorrect policy.
The replay also requires every changed dimension to be declared exactly once;
an event cannot alter mileage or date invisibly.
The event constructors enforce the same value, title, and dimension invariants,
so invalid audit records cannot enter the domain event stream.
Replay uses that shared validator as a defensive boundary as well, keeping
directly supplied event objects subject to the same rules.
`project_warning_threshold_histories` applies the same replay to a complete
maintenance plan, routing each event by title and leaving unrelated items
unchanged. Duplicate item titles and events for unknown items are rejected.
Unsupported event values are rejected with a domain error at the projection
boundary rather than leaking an implementation-level attribute error.

`CustomizeWarningThresholds` is the application command boundary for owner
threshold changes. `RestoreManufacturerWarningThresholds` is the matching
command for returning to canonical values. Both return the updated item with
their audit event so adapters do not need to call domain functions directly.
`ViewWarningThresholdHistory` provides the corresponding query, returning the
effective policy together with its ordered audit events.
It is owner-authorized and rejects non-owner requests with a stable forbidden
error, matching the service-history query boundary. The runtime scenario emits
both the successful owner response and the forbidden non-owner response.
The runtime scenario executes both commands and emits their domain events, so
the catalog entries are backed by runtime evidence as well as unit tests.

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
without status data. Both response shapes declare the same schema version.

Odometer history is append-only. Normal readings are monotonic; a lower value
requires `correction_of`, preserves the original event, and changes the current
projection explicitly.

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
- owner status API versions success and error envelopes consistently;
- odometer corrections preserve history and require explicit linkage;
- invariant confirms unknown data never becomes healthy.
- named application use cases cover three owner-facing queries and six
  owner-facing write interactions;
- runtime observations expose each named use-case execution and outcome;

## Out of scope

Document obligations, authentication, sharing, persistence, browser behavior,
and mechanical diagnosis.
