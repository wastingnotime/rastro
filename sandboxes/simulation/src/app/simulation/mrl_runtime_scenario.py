from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from mrl_simulation_runtime.actors import Actor
from mrl_simulation_runtime.invariants import Invariant
from mrl_simulation_runtime.scenario import ObservatoryEdge, ObservatoryNode, Scenario

from app.domain.maintenance import (
    MaintenanceItem,
    MotorcycleState,
    MaintenanceStatus,
    assess,
    next_action,
    next_actions,
    grouped_actions,
    project_service_history,
    record_service,
    void_service_record,
)
from app.domain.obligations import DocumentObligation, next_owner_actions
from app.domain.odometer import OdometerHistory, current_odometer_reading
from app.application.service_history import (
    ServiceCorrectionForbidden,
    ServiceHistoryState,
    void_service_record_for_owner,
)
from app.application.attention_view import (
    AttentionViewPreferences,
    build_attention_view,
    toggle_group,
)
from app.application.attention_sync import (
    AttentionSyncState,
    merge_preference_snapshots,
    snapshot_preferences,
)
from app.application.owner_status_payload import owner_status_payload
from app.application.owner_status_api import get_owner_status_response
from app.application.service_history_api import get_service_history_response
from app.application.use_cases import (
    CorrectServiceRecord,
    CustomizeWarningThresholds,
    RecordOdometerReading,
    RecordService,
    RestoreManufacturerWarningThresholds,
    SyncAttentionPreferences,
    USE_CASE_CATALOG,
    USE_CASE_IDS,
    USE_CASE_KINDS,
    ViewOwnerStatus,
    ViewServiceHistory,
    ViewWarningThresholdHistory,
)
from app.infrastructure.fakes.attention_preferences import InMemoryAttentionPreferenceStore
from app.simulation.ownership_profiles import (
    daily_commuter,
    long_unused,
    simulate_profile,
    simulate_profile_reminders,
    weekend_rider,
)
from app.simulation.reminders import ReminderPolicy, ReminderTracker


def _emit_use_case(
    context: object,
    name: str,
    actor: str,
    outcome: str,
    results: list[dict[str, str]],
    **details: object,
) -> None:
    """Emit one stable observation shape for every application use case."""
    kind = USE_CASE_KINDS[name].value
    use_case_id = USE_CASE_IDS[name]
    results.append({"id": use_case_id, "name": name, "kind": kind, "outcome": outcome})
    context.emit(
        "use_case_executed",
        name,
        source="application-use-case",
        actor=actor,
        payload={"use_case_id": use_case_id, "kind": kind, "outcome": outcome, **details},
    )


def _emit_use_case_catalog(context: object) -> None:
    context.emit(
        "use_case_catalog",
        "motorcycle-maintenance",
        source="application-use-case",
        actor="owner",
        payload={
            "use_cases": [
                {
                    "name": definition.name,
                    "use_case_id": definition.use_case_id,
                    "kind": definition.kind.value,
                    "purpose": definition.purpose,
                }
                for definition in USE_CASE_CATALOG
            ]
        },
    )


def _emit_use_case_summary(
    context: object, phase: str, results: list[dict[str, str]]
) -> None:
    by_kind = {kind: sum(result["kind"] == kind for result in results) for kind in ("query", "command")}
    by_outcome = {
        outcome: sum(result["outcome"] == outcome for result in results)
        for outcome in ("accepted", "rejected", "succeeded")
    }
    context.emit(
        "use_case_summary",
        phase,
        source="application-use-case",
        actor="owner",
        payload={
            "execution_count": len(results),
            "by_kind": by_kind,
            "by_outcome": by_outcome,
            "use_cases": [result["name"] for result in results],
            "use_case_ids": [result["id"] for result in results],
        },
    )


def _start_owner(context: object) -> None:
    _emit_use_case_catalog(context)
    use_case_results: list[dict[str, str]] = []
    context.emit(
        "domain_observation",
        "motorcycle_status_calculated",
        source="maintenance-status",
        actor="owner",
        payload={"motorcycle": "Honda CB 500X", "odometer_km": 18420},
    )
    motorcycle = MotorcycleState(date(2026, 7, 31), 18420)
    items = [
        MaintenanceItem("Engine oil", interval_km=4000, warning_km=500, last_service_odometer_km=16000),
        MaintenanceItem("Chain inspection", interval_km=3000, warning_km=500, last_service_odometer_km=15900),
    ]
    threshold_customizer = CustomizeWarningThresholds()
    customized_engine_oil, customization_event = threshold_customizer.execute(
        items[0],
        warning_km=1000,
    )
    _emit_use_case(
        context,
        "CustomizeWarningThresholds",
        "owner",
        "succeeded",
        use_case_results,
        maintenance_title=customization_event.maintenance_title,
        changed_dimensions=list(customization_event.changed_dimensions),
    )
    context.emit(
        "domain_event",
        "warning_thresholds_customized",
        source="maintenance-status",
        actor="owner",
        payload={
            "maintenance_title": customization_event.maintenance_title,
            "warning_km": customization_event.warning_km,
            "warning_days": customization_event.warning_days,
            "changed_dimensions": list(customization_event.changed_dimensions),
        },
    )
    restored_engine_oil, restoration_event = RestoreManufacturerWarningThresholds().execute(
        customized_engine_oil,
    )
    _emit_use_case(
        context,
        "RestoreManufacturerWarningThresholds",
        "owner",
        "succeeded",
        use_case_results,
        maintenance_title=restoration_event.maintenance_title,
        changed_dimensions=list(restoration_event.changed_dimensions),
    )
    context.emit(
        "domain_event",
        "warning_thresholds_restored",
        source="maintenance-status",
        actor="owner",
        payload={
            "maintenance_title": restoration_event.maintenance_title,
            "warning_km": restoration_event.manufacturer_warning_km,
            "warning_days": restoration_event.manufacturer_warning_days,
            "changed_dimensions": list(restoration_event.changed_dimensions),
        },
    )
    threshold_history_view = ViewWarningThresholdHistory().execute(
        items[0],
        [customization_event, restoration_event],
        actor_id="owner-1",
        owner_id="owner-1",
    )
    _emit_use_case(
        context,
        "ViewWarningThresholdHistory",
        "owner",
        "succeeded",
        use_case_results,
        maintenance_title=threshold_history_view.effective_item.title,
        event_count=len(threshold_history_view.events),
    )
    context.emit(
        "threshold_history_view",
        threshold_history_view.effective_item.title,
        source="maintenance-status",
        actor="owner",
        payload={
            "event_count": len(threshold_history_view.events),
            "warning_km": threshold_history_view.effective_item.warning_km,
            "warning_days": threshold_history_view.effective_item.warning_days,
        },
    )
    items[0] = restored_engine_oil
    assessments = [assess(item, motorcycle) for item in items]
    action = next_action(items, motorcycle)
    for assessment in assessments:
        context.emit(
            "maintenance_status",
            assessment.title,
            source="maintenance-status",
            actor="owner",
            payload={"status": assessment.status.value, "remaining_km": assessment.remaining_km},
        )
    context.emit(
        "next_action",
        action.title if action else "nothing_due",
        source="maintenance-status",
        actor="owner",
        payload={"status": action.status.value if action else None},
    )
    grouped_items = items + [
        MaintenanceItem(
            "Brake inspection",
            interval_days=30,
            warning_days=7,
            last_service_date=date(2026, 7, 8),
        )
    ]
    grouped = next_actions(grouped_items, motorcycle)
    context.emit(
        "next_actions_grouped",
        "maintenance_attention",
        source="maintenance-status",
        actor="owner",
        payload={"items": [assessment.title for assessment in grouped]},
    )
    attention_view = build_attention_view(
        grouped_actions(
            grouped_items
            + [
                MaintenanceItem(
                    "Tire inspection",
                    interval_km=1000,
                    last_service_odometer_km=17000,
                )
            ],
            motorcycle,
        )
    )
    context.emit(
        "attention_view",
        "owner_attention_view",
        source="attention-presenter",
        actor="owner",
        payload={
            "groups": [
                {
                    "status": group.status,
                    "items": list(group.item_titles),
                    "expanded": group.expanded,
                }
                for group in attention_view
            ]
        },
    )
    persisted_view = build_attention_view(
        grouped_actions(
            grouped_items
            + [
                MaintenanceItem(
                    "Tire inspection",
                    interval_km=1000,
                    last_service_odometer_km=17000,
                )
            ],
            motorcycle,
        ),
        preferences=toggle_group(AttentionViewPreferences("moto-1"), "approaching_due"),
        scope_id="moto-1",
    )
    context.emit(
        "attention_view_persisted",
        "owner_attention_preference",
        source="attention-presenter",
        actor="owner",
        payload={"expanded": [group.status for group in persisted_view if group.expanded]},
    )
    local_snapshot = snapshot_preferences(
        AttentionViewPreferences("moto-1", frozenset({"approaching_due"})),
        owner_id="owner-1",
        revision=2,
        device_id="phone",
    )
    remote_snapshot = snapshot_preferences(
        AttentionViewPreferences("moto-1", frozenset({"due", "approaching_due"})),
        owner_id="owner-1",
        revision=3,
        device_id="web",
    )
    merged_snapshot = merge_preference_snapshots(local_snapshot, remote_snapshot)
    context.emit(
        "attention_preference_sync",
        "moto-1",
        source="attention-sync",
        actor="owner",
        payload={
            "device_id": merged_snapshot.device_id,
            "revision": merged_snapshot.revision,
            "expanded_statuses": sorted(merged_snapshot.expanded_statuses),
        },
    )
    _, sync_response = SyncAttentionPreferences().execute(
        AttentionSyncState("owner-1", (local_snapshot,)),
        actor_id="owner-1",
        incoming=remote_snapshot,
    )
    _emit_use_case(
        context,
        "SyncAttentionPreferences",
        "owner-1",
        "accepted" if sync_response.accepted else "rejected",
        use_case_results,
        accepted=sync_response.accepted,
        code=sync_response.code,
    )
    context.emit(
        "attention_preference_sync_response",
        sync_response.code,
        source="attention-sync",
        actor="owner-1",
        payload={"accepted": sync_response.accepted, "message": sync_response.message},
    )
    preference_store = InMemoryAttentionPreferenceStore()
    stored_snapshot = preference_store.save(remote_snapshot)
    context.emit(
        "attention_preference_stored",
        stored_snapshot.scope_id,
        source="account-preference-store",
        actor="owner-1",
        payload={
            "revision": stored_snapshot.revision,
            "device_id": stored_snapshot.device_id,
        },
    )
    obligations = [
        DocumentObligation("Licensing renewal", date(2026, 8, 24), warning_days=30)
    ]
    owner_actions = next_owner_actions(items, obligations, motorcycle)
    context.emit(
        "owner_attention_grouped",
        "owner_attention",
        source="maintenance-status",
        actor="owner",
        payload={"items": [assessment.title for assessment in owner_actions]},
    )
    dashboard = ViewOwnerStatus().execute(
        motorcycle_id="moto-1",
        motorcycle=motorcycle,
        maintenance_items=items,
        obligations=obligations,
    )
    _emit_use_case(
        context,
        "ViewOwnerStatus",
        "owner",
        "succeeded",
        use_case_results,
        attention_count=len(dashboard.attention),
    )
    context.emit(
        "owner_status_view",
        dashboard.motorcycle_id,
        source="owner-dashboard-query",
        actor="owner",
        payload={
            "odometer_km": dashboard.odometer_km,
            "attention": [
                {"title": item.title, "source": item.source, "status": item.status.value}
                for item in dashboard.attention
            ],
            "next_action_titles": list(dashboard.next_action_titles),
        },
    )
    context.emit(
        "owner_status_payload",
        dashboard.motorcycle_id,
        source="owner-status-adapter",
        actor="owner",
        payload=owner_status_payload(dashboard),
    )
    api_response = get_owner_status_response(
        actor_id="owner-1",
        owner_id="owner-1",
        motorcycle_id="moto-1",
        motorcycle=motorcycle,
        maintenance_items=items,
        obligations=obligations,
    )
    context.emit(
        "owner_status_api_response",
        "/api/v1/motorcycles/{motorcycle_id}/maintenance-status",
        source="owner-status-api",
        actor="owner-1",
        payload={"status_code": api_response.status_code, "schema_version": api_response.body["schema_version"]},
    )
    reminder_tracker = ReminderTracker(ReminderPolicy(repeat_every_days=14))
    first_reminders = reminder_tracker.evaluate(date(2026, 7, 31), owner_actions)
    suppressed_reminders = reminder_tracker.evaluate(date(2026, 8, 1), owner_actions)
    context.emit(
        "reminder_evaluation",
        "owner_attention_reminders",
        source="reminder-policy",
        actor="owner",
        payload={
            "first_reminders": first_reminders,
            "next_day_reminders": suppressed_reminders,
        },
    )
    service_recorder = RecordService()
    serviced_items, service_event = service_recorder.execute(
        items,
        completed_titles=["Chain inspection"],
        serviced_at=date(2026, 7, 31),
        odometer_km=18420,
        provider_name="Local mechanic",
        notes="Chain adjusted",
    )
    _emit_use_case(
        context,
        "RecordService",
        "owner",
        "succeeded",
        use_case_results,
        service_id=service_event.service_id,
        completed_items=list(service_event.completed_titles),
    )
    context.emit(
        "domain_event",
        "service_recorded",
        source="maintenance-status",
        actor="owner",
        payload={
            "completed_items": list(service_event.completed_titles),
            "serviced_at": service_event.serviced_at.isoformat(),
            "odometer_km": service_event.odometer_km,
            "provider_name": service_event.provider_name,
        },
    )
    after_service = assess(serviced_items[1], motorcycle)
    context.emit(
        "maintenance_status",
        after_service.title,
        source="maintenance-status",
        actor="owner",
        payload={"status": after_service.status.value, "remaining_km": after_service.remaining_km},
    )
    _, corrected_record = service_recorder.execute(
        items,
        completed_titles=["Chain inspection"],
        serviced_at=date(2026, 8, 1),
        odometer_km=99999,
        service_id="service-correction",
    )
    void_event = void_service_record("service-correction", "Incorrect odometer")
    corrected_items = project_service_history(
        items,
        [service_event, corrected_record],
        [void_event],
    )
    context.emit(
        "domain_event",
        "service_record_voided",
        source="maintenance-status",
        actor="owner",
        payload={"service_id": void_event.service_id, "reason": void_event.reason},
    )
    corrected_assessment = assess(corrected_items[1], motorcycle)
    context.emit(
        "maintenance_status",
        "Chain inspection after correction",
        source="maintenance-status",
        actor="owner",
        payload={
            "status": corrected_assessment.status.value,
            "remaining_km": corrected_assessment.remaining_km,
        },
    )
    corrected_history = ServiceHistoryState(
        "moto-1",
        "owner-1",
        records=(service_event, corrected_record),
        voided_records=(void_event,),
    )
    visible_after_correction = ViewServiceHistory().execute(
        corrected_history,
        actor_id="owner-1",
    )
    _emit_use_case(
        context,
        "ViewServiceHistory",
        "owner-1",
        "succeeded",
        use_case_results,
        record_count=len(visible_after_correction),
        voided_count=len(corrected_history.voided_records),
    )
    history_api_response = get_service_history_response(
        actor_id="owner-1",
        state=corrected_history,
    )
    context.emit(
        "service_history_api_response",
        "/api/v1/motorcycles/{motorcycle_id}/service-history",
        source="service-history-api",
        actor="owner-1",
        payload={
            "status_code": history_api_response.status_code,
            "schema_version": history_api_response.body["schema_version"],
            "record_count": len(history_api_response.body["records"]),
        },
    )
    forbidden_history_api_response = get_service_history_response(
        actor_id="mechanic-1",
        state=corrected_history,
    )
    context.emit(
        "service_history_api_response",
        "/api/v1/motorcycles/{motorcycle_id}/service-history",
        source="service-history-api",
        actor="mechanic-1",
        payload={
            "status_code": forbidden_history_api_response.status_code,
            "schema_version": forbidden_history_api_response.body["schema_version"],
            "code": forbidden_history_api_response.body["code"],
            "records_exposed": "records" in forbidden_history_api_response.body,
        },
    )
    history = ServiceHistoryState("moto-1", "owner-1", records=(service_event,))
    visible_history = ViewServiceHistory().execute(history, actor_id="owner-1")
    _emit_use_case(
        context,
        "ViewServiceHistory",
        "owner-1",
        "succeeded",
        use_case_results,
        record_count=len(visible_history),
    )
    try:
        void_service_record_for_owner(history, "mechanic-1", service_event.service_id, "Correction")
    except ServiceCorrectionForbidden as error:
        context.emit(
            "application_error",
            error.code,
            source="service-history-command",
            actor="mechanic-1",
            payload={"message": str(error)},
        )
    _, correction_response = CorrectServiceRecord().execute(
        history,
        actor_id="mechanic-1",
        service_id=service_event.service_id,
        reason="Correction",
    )
    _emit_use_case(
        context,
        "CorrectServiceRecord",
        "mechanic-1",
        "accepted" if correction_response.accepted else "rejected",
        use_case_results,
        accepted=correction_response.accepted,
        code=correction_response.code,
    )
    context.emit(
        "application_response",
        correction_response.code,
        source="service-history-command",
        actor="mechanic-1",
        payload={
            "accepted": correction_response.accepted,
            "message": correction_response.message,
        },
    )
    _emit_use_case_summary(context, "owner-start", use_case_results)
    profile_item = MaintenanceItem(
        "Engine oil",
        interval_km=4000,
        warning_km=500,
        last_service_odometer_km=18000,
    )
    for profile in (daily_commuter(), weekend_rider(), long_unused()):
        result = simulate_profile(
            profile,
            start_date=date(2026, 1, 1),
            days=365,
            starting_odometer_km=18000,
            item=profile_item,
        )
        context.emit(
            "profile_evidence",
            result.profile,
            source="ownership-profiles",
            actor="owner",
            payload={
                "days": result.days,
                "unknown_days": result.unknown_days,
                "attention_days": result.attention_days,
                "status_counts": result.status_counts,
            },
        )
        for cadence in (7, 14, 30):
            reminder_result = simulate_profile_reminders(
                profile,
                start_date=date(2026, 1, 1),
                days=365,
                starting_odometer_km=18000,
                item=profile_item,
                cadence_days=cadence,
            )
            context.emit(
                "reminder_profile_evidence",
                f"{result.profile}_{cadence}d",
                source="reminder-policy",
                actor="owner",
                payload={"reminder_count": reminder_result.reminder_count},
            )


class OwnerBehavior:
    def on_start(self, context: object) -> None:
        context.scheduler.schedule_after(
            context,
            timedelta(seconds=5),
            _start_owner,
            name="owner_start_flow",
            source="owner",
        )


def _unknown_is_not_healthy(context: object) -> bool:
    item = MaintenanceItem("Unconfigured item", interval_km=4000, last_service_odometer_km=None)
    result = assess(item, MotorcycleState(date(2026, 7, 31), 18420))
    return result.status == MaintenanceStatus.UNKNOWN


def _stale_mileage_is_unknown(context: object) -> bool:
    item = MaintenanceItem(
        "Stale reading item",
        interval_km=4000,
        last_service_odometer_km=15000,
    )
    motorcycle = MotorcycleState(date(2026, 7, 31), 18000, date(2026, 5, 1))
    return assess(item, motorcycle).status == MaintenanceStatus.UNKNOWN


def _completed_obligation_is_not_actionable(context: object) -> bool:
    obligation = DocumentObligation(
        "Completed insurance",
        date(2026, 7, 1),
        completed_at=date(2026, 6, 30),
    )
    return not next_owner_actions([], [obligation], MotorcycleState(date(2026, 7, 31), None))


def _long_unused_profile_becomes_unknown(context: object) -> bool:
    result = simulate_profile(
        long_unused(),
        start_date=date(2026, 1, 1),
        days=365,
        starting_odometer_km=18000,
        item=MaintenanceItem("Engine oil", interval_km=4000, last_service_odometer_km=18000),
    )
    return result.unknown_days == 274


def _voided_correction_restores_active_baseline(context: object) -> bool:
    item = MaintenanceItem("Chain inspection", interval_km=3000, last_service_odometer_km=15000)
    _, first = record_service(
        [item], ["Chain inspection"], date(2026, 7, 1), 18000, service_id="service-a"
    )
    _, correction = record_service(
        [item], ["Chain inspection"], date(2026, 7, 15), 19000, service_id="service-b"
    )
    projected = project_service_history(
        [item], [first, correction], [void_service_record("service-b", "Incorrect odometer")]
    )
    return projected[0].last_service_odometer_km == 18000


def _non_owner_correction_is_denied(context: object) -> bool:
    state = ServiceHistoryState("moto-1", "owner-1")
    try:
        void_service_record_for_owner(state, "mechanic-1", "service-a", "Correction")
    except PermissionError:
        return True
    return False


def _same_day_due_items_are_grouped(context: object) -> bool:
    items = [
        MaintenanceItem("Brake inspection", interval_days=30, last_service_date=date(2026, 7, 1)),
        MaintenanceItem("Licensing renewal", interval_days=30, last_service_date=date(2026, 7, 1)),
    ]
    actions = next_actions(items, MotorcycleState(date(2026, 7, 31), None))
    return [action.title for action in actions] == ["Brake inspection", "Licensing renewal"]


def _mixed_urgency_groups_keep_priority_context(context: object) -> bool:
    items = [
        MaintenanceItem("Engine oil", interval_km=4000, last_service_odometer_km=14000),
        MaintenanceItem("Chain inspection", interval_km=3000, last_service_odometer_km=15420),
        MaintenanceItem(
            "Brake inspection",
            interval_days=30,
            warning_days=7,
            last_service_date=date(2026, 7, 4),
        ),
    ]
    groups = grouped_actions(items, MotorcycleState(date(2026, 7, 31), 18420))
    return [group.status.value for group in groups] == ["overdue", "due", "approaching_due"]


def _odometer_correction_preserves_history(context: object) -> bool:
    recorder = RecordOdometerReading()
    use_case_results: list[dict[str, str]] = []
    history, original = recorder.execute(
        OdometerHistory(),
        reading_id="reading-1",
        odometer_km=18000,
        recorded_at=date(2026, 7, 1),
    )
    history, correction = recorder.execute(
        history,
        reading_id="correction-1",
        odometer_km=17500,
        recorded_at=date(2026, 7, 2),
        correction_of=original.reading_id,
    )
    _emit_use_case(
        context,
        "RecordOdometerReading",
        "owner",
        "succeeded",
        use_case_results,
        reading_count=len(history.readings),
        corrected=True,
    )
    _emit_use_case_summary(context, "odometer-invariant", use_case_results)
    return len(history.readings) == 2 and current_odometer_reading(history) == correction


def create_simulation() -> Scenario:
    return Scenario(
        name="motorcycle-maintenance-status",
        seed=500,
        initial_time=datetime(2026, 7, 31, tzinfo=timezone.utc),
        run_id="maintenance-status-first-slice",
        actors=[Actor(name="owner", behavior=OwnerBehavior())],
        invariants=[
            Invariant("unknown_data_is_not_healthy", _unknown_is_not_healthy),
            Invariant("stale_mileage_is_unknown", _stale_mileage_is_unknown),
            Invariant("completed_obligation_is_not_actionable", _completed_obligation_is_not_actionable),
            Invariant("long_unused_profile_becomes_unknown", _long_unused_profile_becomes_unknown),
            Invariant("voided_correction_restores_active_baseline", _voided_correction_restores_active_baseline),
            Invariant("non_owner_correction_is_denied", _non_owner_correction_is_denied),
            Invariant("same_day_due_items_are_grouped", _same_day_due_items_are_grouped),
            Invariant("mixed_urgency_groups_keep_priority_context", _mixed_urgency_groups_keep_priority_context),
            Invariant("odometer_correction_preserves_history", _odometer_correction_preserves_history),
        ],
        observatory_nodes=[
            ObservatoryNode("owner", "Motorcycle owner", "actor", "domain"),
            ObservatoryNode("status", "Maintenance status", "domain", "domain"),
            ObservatoryNode("action", "Next action", "projection", "application"),
            *[
                ObservatoryNode(
                    definition.use_case_id,
                    definition.name,
                    "use_case",
                    "application",
                    realm=definition.kind.value,
                    description=definition.purpose,
                )
                for definition in USE_CASE_CATALOG
            ],
        ],
        observatory_edges=[
            ObservatoryEdge("owner", "status", "checks"),
            ObservatoryEdge("status", "action", "prioritizes"),
            *[
                ObservatoryEdge("owner", definition.use_case_id, "invokes")
                for definition in USE_CASE_CATALOG
            ],
        ],
    )
