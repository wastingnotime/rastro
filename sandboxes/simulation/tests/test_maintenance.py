import unittest
from datetime import date

from app.domain.maintenance import (
    MaintenanceAssessment,
    MaintenanceItem,
    MaintenanceStatus,
    MotorcycleState,
    ServiceRecorded,
    ServiceRecordVoided,
    ThresholdSource,
    WarningThresholdsCustomized,
    WarningThresholdsRestored,
    assess,
    complete_service,
    customize_warning_thresholds,
    customize_warning_thresholds_with_event,
    restore_manufacturer_warning_thresholds,
    restore_manufacturer_warning_thresholds_with_event,
    project_warning_threshold_history,
    grouped_actions,
    record_service,
    project_service_history,
    void_service_record,
    next_action,
    next_actions,
)
from app.domain.obligations import (
    DocumentObligation,
    assess_obligation,
    next_obligation_actions,
    next_owner_actions,
)
from app.domain.odometer import OdometerHistory, current_odometer_reading, record_odometer_reading
from app.application.service_history import (
    CorrectionCommand,
    ServiceCorrectionAlreadyVoided,
    ServiceCorrectionForbidden,
    ServiceCorrectionNotFound,
    ServiceHistoryState,
    ServiceHistoryViewForbidden,
    handle_correction,
    void_service_record_for_owner,
)
from app.application.attention_view import (
    AttentionViewPreferences,
    build_attention_view,
    toggle_group,
)
from app.application.owner_dashboard import build_owner_status
from app.application.owner_status_payload import owner_status_payload
from app.application.owner_status_api import OWNER_STATUS_ROUTE, get_owner_status_response
from app.application.service_history_api import SERVICE_HISTORY_ROUTE, get_service_history_response
from app.application.attention_sync import (
    AttentionSyncState,
    handle_preference_sync,
    merge_preference_snapshots,
    preferences_from_snapshot,
    snapshot_preferences,
)
from app.application.use_cases import (
    CorrectServiceRecord,
    RecordOdometerReading,
    RecordService,
    SyncAttentionPreferences,
    ViewOwnerStatus,
    ViewServiceHistory,
)
from app.application.use_cases import (
    USE_CASE_CATALOG,
    USE_CASE_IDS,
    USE_CASE_KINDS,
    UseCaseDefinition,
    UseCaseKind,
    index_use_case_catalog,
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


class MaintenanceStatusTests(unittest.TestCase):
    def test_owner_warning_override_is_provenanced_and_changes_status(self):
        manufacturer_item = MaintenanceItem(
            "Engine oil",
            interval_km=4000,
            warning_km=500,
            last_service_odometer_km=15000,
        )
        owner_item = customize_warning_thresholds(manufacturer_item, warning_km=1000)
        motorcycle = MotorcycleState(date(2026, 7, 31), 18420)
        self.assertEqual(manufacturer_item.warning_source, ThresholdSource.MANUFACTURER)
        self.assertEqual(manufacturer_item.manufacturer_warning_km, 500)
        self.assertEqual(manufacturer_item.manufacturer_warning_days, 0)
        self.assertEqual(owner_item.warning_source, ThresholdSource.MIXED)
        self.assertEqual(owner_item.warning_km_source, ThresholdSource.OWNER)
        self.assertEqual(
            owner_item.warning_days_source,
            ThresholdSource.MANUFACTURER,
        )
        self.assertEqual(assess(manufacturer_item, motorcycle).status, MaintenanceStatus.OK)
        self.assertEqual(
            assess(owner_item, motorcycle).status,
            MaintenanceStatus.APPROACHING_DUE,
        )
        self.assertEqual(
            assess(owner_item, motorcycle).warning_source,
            ThresholdSource.MIXED,
        )

    def test_warning_override_rejects_missing_or_negative_values(self):
        item = MaintenanceItem("Engine oil", interval_km=4000)
        with self.assertRaises(ValueError):
            customize_warning_thresholds(item)
        with self.assertRaises(ValueError):
            customize_warning_thresholds(item, warning_km=-1)
        with self.assertRaises(ValueError):
            customize_warning_thresholds(item, warning_days=-1)

    def test_maintenance_item_rejects_invalid_policy_values(self):
        with self.assertRaises(ValueError):
            MaintenanceItem("Engine oil", interval_km=-1)
        with self.assertRaises(ValueError):
            MaintenanceItem("Engine oil", warning_days=-1)
        with self.assertRaises(ValueError):
            MaintenanceItem("Engine oil", manufacturer_warning_km=-1)
        with self.assertRaises(ValueError):
            MaintenanceItem(
                "Engine oil",
                warning_km=500,
                manufacturer_warning_km=1000,
            )
        with self.assertRaises(ValueError):
            MaintenanceItem(
                "Engine oil",
                warning_days=7,
                manufacturer_warning_days=30,
            )
        with self.assertRaises(ValueError):
            MaintenanceItem("")

    def test_warning_override_event_preserves_before_and_after_thresholds(self):
        item = MaintenanceItem("Engine oil", interval_km=4000, warning_km=500)
        updated, event = customize_warning_thresholds_with_event(
            item,
            warning_km=1000,
        )
        self.assertIsInstance(event, WarningThresholdsCustomized)
        self.assertEqual(event.maintenance_title, "Engine oil")
        self.assertEqual((event.previous_warning_km, event.warning_km), (500, 1000))
        self.assertEqual(event.changed_dimensions, ("mileage",))
        self.assertEqual(updated.warning_km, event.warning_km)
        self.assertEqual(event.previous_warning_days, event.warning_days)

    def test_owner_warning_override_can_restore_manufacturer_policy(self):
        item = MaintenanceItem("Engine oil", interval_km=4000, warning_km=500)
        customized = customize_warning_thresholds(item, warning_km=1000)
        self.assertEqual(customized.manufacturer_warning_km, 500)
        self.assertEqual(customized.manufacturer_warning_days, 0)
        restored = restore_manufacturer_warning_thresholds(
            customized,
        )
        self.assertEqual(restored.warning_km, 500)
        self.assertEqual(restored.warning_days, 0)
        self.assertEqual(restored.warning_source, ThresholdSource.MANUFACTURER)
        with self.assertRaises(ValueError):
            restore_manufacturer_warning_thresholds(
                customized,
                warning_km=-1,
                warning_days=0,
            )

    def test_manufacturer_restore_event_preserves_before_and_after_thresholds(self):
        customized = customize_warning_thresholds(
            MaintenanceItem("Engine oil", interval_km=4000, warning_km=500),
            warning_km=1000,
        )
        restored, event = restore_manufacturer_warning_thresholds_with_event(
            customized,
            warning_km=500,
            warning_days=0,
        )
        self.assertIsInstance(event, WarningThresholdsRestored)
        self.assertEqual((event.previous_warning_km, event.manufacturer_warning_km), (1000, 500))
        self.assertEqual(event.changed_dimensions, ("mileage",))
        self.assertEqual(restored.warning_source, ThresholdSource.MANUFACTURER)

    def test_threshold_event_history_replays_customization_and_restore(self):
        item = MaintenanceItem("Engine oil", interval_km=4000, warning_km=500)
        customized, customization_event = customize_warning_thresholds_with_event(
            item,
            warning_km=1000,
        )
        restored, restoration_event = restore_manufacturer_warning_thresholds_with_event(
            customized,
        )

        self.assertEqual(
            project_warning_threshold_history(item, [customization_event]),
            customized,
        )
        self.assertEqual(
            project_warning_threshold_history(
                item,
                [customization_event, restoration_event],
            ),
            restored,
        )

    def test_threshold_event_history_rejects_gaps_and_wrong_items(self):
        item = MaintenanceItem("Engine oil", warning_km=500)
        _, event = customize_warning_thresholds_with_event(item, warning_km=1000)
        with self.assertRaises(ValueError):
            project_warning_threshold_history(item, [event, event])
        with self.assertRaises(ValueError):
            project_warning_threshold_history(
                item,
                [WarningThresholdsCustomized("Brake", 500, 0, 1000, 0)],
            )

    def test_named_owner_status_use_case_returns_attention(self):
        view = ViewOwnerStatus().execute(
            motorcycle_id="moto-1",
            motorcycle=MotorcycleState(date(2026, 7, 31), 18500),
            maintenance_items=[
                MaintenanceItem(
                    interval_km=4000,
                    warning_km=500,
                    last_service_odometer_km=15000,
                    title="Engine oil",
                )
            ],
            obligations=[],
        )
        self.assertEqual(view.next_action_titles, ("Engine oil",))

    def test_use_case_catalog_classifies_query_and_commands(self):
        self.assertEqual(USE_CASE_KINDS["ViewOwnerStatus"], UseCaseKind.QUERY)
        self.assertEqual(USE_CASE_IDS["ViewOwnerStatus"], "view-owner-status")
        self.assertEqual(
            {name for name, kind in USE_CASE_KINDS.items() if kind == UseCaseKind.COMMAND},
            {
                "RecordService",
                "CorrectServiceRecord",
                "SyncAttentionPreferences",
                "RecordOdometerReading",
            },
        )
        self.assertTrue(all(definition.purpose for definition in USE_CASE_CATALOG))

    def test_use_case_definition_rejects_blank_identity_or_purpose(self):
        with self.assertRaises(ValueError):
            UseCaseDefinition("view-owner-status", "", UseCaseKind.QUERY, "Shows status")
        with self.assertRaises(ValueError):
            UseCaseDefinition("view-owner-status", "ViewOwnerStatus", UseCaseKind.QUERY, "")
        with self.assertRaises(ValueError):
            UseCaseDefinition("", "ViewOwnerStatus", UseCaseKind.QUERY, "Shows status")

    def test_use_case_catalog_rejects_duplicate_names_and_ids(self):
        duplicate_name = (
            UseCaseDefinition("one", "SameName", UseCaseKind.QUERY, "First"),
            UseCaseDefinition("two", "SameName", UseCaseKind.COMMAND, "Second"),
        )
        duplicate_id = (
            UseCaseDefinition("same", "FirstName", UseCaseKind.QUERY, "First"),
            UseCaseDefinition("same", "SecondName", UseCaseKind.COMMAND, "Second"),
        )
        with self.assertRaises(ValueError):
            index_use_case_catalog(duplicate_name)
        with self.assertRaises(ValueError):
            index_use_case_catalog(duplicate_id)

    def test_named_service_correction_use_case_preserves_response_boundary(self):
        state = ServiceHistoryState(
            "moto-1",
            "owner-1",
            records=(ServiceRecorded(date(2026, 7, 1), 18000, ("oil",), service_id="service-1"),),
        )
        updated, response = CorrectServiceRecord().execute(
            state,
            actor_id="owner-1",
            service_id="service-1",
            reason="entered wrong mileage",
        )
        self.assertTrue(response.accepted)
        self.assertEqual(updated.voided_records[0].service_id, "service-1")

    def test_named_service_history_query_is_owner_authorized(self):
        record = ServiceRecorded(date(2026, 7, 1), 18000, ("oil",), service_id="service-1")
        state = ServiceHistoryState("moto-1", "owner-1", records=(record,))
        self.assertEqual(ViewServiceHistory().execute(state, actor_id="owner-1"), (record,))
        with self.assertRaises(ServiceHistoryViewForbidden):
            ViewServiceHistory().execute(state, actor_id="mechanic-1")

    def test_service_history_query_hides_voided_records_but_keeps_audit_event(self):
        active = ServiceRecorded(date(2026, 7, 1), 18000, ("oil",), service_id="active")
        voided = ServiceRecorded(date(2026, 7, 2), 18100, ("oil",), service_id="voided")
        state = ServiceHistoryState(
            "moto-1",
            "owner-1",
            records=(active, voided),
            voided_records=(ServiceRecordVoided("voided", "wrong mileage"),),
        )
        self.assertEqual(ViewServiceHistory().execute(state, actor_id="owner-1"), (active,))
        self.assertEqual(state.voided_records[0].reason, "wrong mileage")

    def test_named_preference_sync_use_case_delegates_owner_scope(self):
        incoming = snapshot_preferences(
            AttentionViewPreferences("moto-1", frozenset({"overdue"})),
            owner_id="owner-1",
            revision=1,
            device_id="phone",
        )
        state, response = SyncAttentionPreferences().execute(
            AttentionSyncState("owner-1"),
            actor_id="owner-1",
            incoming=incoming,
        )
        self.assertTrue(response.accepted)
        self.assertEqual(state.snapshots, (incoming,))

    def test_named_odometer_use_case_appends_reading(self):
        history, reading = RecordOdometerReading().execute(
            OdometerHistory(),
            reading_id="reading-1",
            odometer_km=18000,
            recorded_at=date(2026, 7, 31),
        )
        self.assertEqual(reading.value_km, 18000)
        self.assertEqual(history.readings, (reading,))

    def test_named_service_use_case_records_selected_items(self):
        items = [
            MaintenanceItem("Engine oil", interval_km=4000, last_service_odometer_km=14000),
            MaintenanceItem("Chain inspection", interval_km=3000, last_service_odometer_km=15900),
        ]
        updated, event = RecordService().execute(
            items,
            completed_titles=["Chain inspection"],
            serviced_at=date(2026, 7, 31),
            odometer_km=18420,
            service_id="service-1",
        )
        self.assertEqual(event.service_id, "service-1")
        self.assertEqual(updated[0].last_service_odometer_km, 14000)
        self.assertEqual(updated[1].last_service_odometer_km, 18420)

    def test_mileage_only_is_ok_outside_warning_window(self):
        result = assess(
            MaintenanceItem(interval_km=4000, warning_km=500, last_service_odometer_km=15000, title="oil"),
            MotorcycleState(date(2026, 7, 31), 18000),
        )
        self.assertEqual(result.status, MaintenanceStatus.OK)
        self.assertEqual(result.remaining_km, 1000)

    def test_mileage_only_approaches_due(self):
        result = assess(
            MaintenanceItem(interval_km=4000, warning_km=500, last_service_odometer_km=15000, title="oil"),
            MotorcycleState(date(2026, 7, 31), 18500),
        )
        self.assertEqual(result.status, MaintenanceStatus.APPROACHING_DUE)

    def test_date_only_becomes_overdue(self):
        result = assess(
            MaintenanceItem(interval_days=30, warning_days=7, last_service_date=date(2026, 6, 1), title="inspection"),
            MotorcycleState(date(2026, 7, 5), None),
        )
        self.assertEqual(result.status, MaintenanceStatus.OVERDUE)
        self.assertEqual(result.remaining_days, -4)

    def test_combined_interval_uses_first_due_dimension(self):
        result = assess(
            MaintenanceItem(
                interval_km=4000,
                interval_days=30,
                warning_km=500,
                warning_days=7,
                last_service_odometer_km=15000,
                last_service_date=date(2026, 7, 1),
                title="oil",
            ),
            MotorcycleState(date(2026, 7, 20), 18500),
        )
        self.assertEqual(result.status, MaintenanceStatus.APPROACHING_DUE)
        self.assertEqual(result.remaining_km, 500)
        self.assertEqual(result.remaining_days, 11)

    def test_missing_baseline_is_unknown(self):
        result = assess(
            MaintenanceItem(interval_km=4000, title="oil"),
            MotorcycleState(date(2026, 7, 31), 18000),
        )
        self.assertEqual(result.status, MaintenanceStatus.UNKNOWN)

    def test_stale_odometer_makes_mileage_status_unknown(self):
        result = assess(
            MaintenanceItem(
                interval_km=4000,
                title="oil",
                last_service_odometer_km=15000,
            ),
            MotorcycleState(date(2026, 7, 31), 18000, date(2026, 5, 1)),
        )
        self.assertEqual(result.status, MaintenanceStatus.UNKNOWN)

    def test_stale_odometer_threshold_is_configurable(self):
        state = MotorcycleState(date(2026, 7, 31), 18000, date(2026, 7, 1))
        item = MaintenanceItem(
            interval_km=4000,
            title="oil",
            last_service_odometer_km=15000,
        )
        self.assertEqual(
            assess(item, state, odometer_stale_after_days=30).status,
            MaintenanceStatus.OK,
        )
        self.assertEqual(
            assess(item, state, odometer_stale_after_days=29).status,
            MaintenanceStatus.UNKNOWN,
        )

    def test_disabled_item_has_no_next_action(self):
        item = MaintenanceItem(interval_km=100, last_service_odometer_km=0, title="old", enabled=False)
        self.assertIsNone(next_action([item], MotorcycleState(date(2026, 7, 31), 1000)))

    def test_next_action_prioritizes_overdue(self):
        items = [
            MaintenanceItem(interval_km=4000, warning_km=500, last_service_odometer_km=15000, title="oil"),
            MaintenanceItem(interval_km=3000, warning_km=500, last_service_odometer_km=15000, title="chain"),
        ]
        action = next_action(items, MotorcycleState(date(2026, 7, 31), 18420))
        self.assertEqual(action.title, "chain")
        self.assertEqual(action.status, MaintenanceStatus.OVERDUE)

    def test_next_actions_groups_items_at_highest_urgency(self):
        items = [
            MaintenanceItem(
                interval_km=3000,
                warning_km=500,
                last_service_odometer_km=15900,
                title="Chain inspection",
            ),
            MaintenanceItem(
                interval_days=30,
                warning_days=7,
                last_service_date=date(2026, 7, 8),
                title="Brake inspection",
            ),
            MaintenanceItem(
                interval_km=4000,
                warning_km=500,
                last_service_odometer_km=16000,
                title="Engine oil",
            ),
        ]
        actions = next_actions(items, MotorcycleState(date(2026, 7, 31), 18420))
        self.assertEqual([action.title for action in actions], ["Brake inspection", "Chain inspection"])
        self.assertTrue(all(action.status == MaintenanceStatus.APPROACHING_DUE for action in actions))

    def test_same_day_due_items_are_grouped_together(self):
        items = [
            MaintenanceItem(
                "Brake inspection",
                interval_days=30,
                last_service_date=date(2026, 7, 1),
            ),
            MaintenanceItem(
                "Licensing renewal",
                interval_days=30,
                last_service_date=date(2026, 7, 1),
            ),
        ]
        actions = next_actions(items, MotorcycleState(date(2026, 7, 31), None))
        self.assertEqual([action.title for action in actions], ["Brake inspection", "Licensing renewal"])
        self.assertTrue(all(action.status == MaintenanceStatus.DUE for action in actions))

    def test_mixed_urgency_groups_preserve_priority_and_context(self):
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
        self.assertEqual(
            [group.status for group in groups],
            [MaintenanceStatus.OVERDUE, MaintenanceStatus.DUE, MaintenanceStatus.APPROACHING_DUE],
        )
        self.assertEqual([item.title for item in groups[0].items], ["Engine oil"])
        self.assertEqual([item.title for item in groups[1].items], ["Chain inspection"])
        self.assertEqual([item.title for item in groups[2].items], ["Brake inspection"])

    def test_attention_view_expands_primary_and_collapses_lower_priority_groups(self):
        groups = grouped_actions(
            [
                MaintenanceItem("Engine oil", interval_km=4000, last_service_odometer_km=14000),
                MaintenanceItem("Chain inspection", interval_km=3000, last_service_odometer_km=15420),
            ],
            MotorcycleState(date(2026, 7, 31), 18420),
        )
        view = build_attention_view(groups)
        self.assertEqual([group.expanded for group in view], [True, False])

        all_expanded = build_attention_view(groups, expand_all=True)
        self.assertTrue(all(group.expanded for group in all_expanded))

    def test_attention_view_preferences_persist_selected_group_expansion(self):
        groups = grouped_actions(
            [
                MaintenanceItem("Engine oil", interval_km=4000, last_service_odometer_km=14000),
                MaintenanceItem("Chain inspection", interval_km=3000, last_service_odometer_km=15420),
            ],
            MotorcycleState(date(2026, 7, 31), 18420),
        )
        preferences = toggle_group(AttentionViewPreferences(), "due")
        view = build_attention_view(groups, preferences=preferences)
        self.assertEqual([group.expanded for group in view], [True, True])
        collapsed = toggle_group(preferences, "due")
        self.assertEqual(
            [group.expanded for group in build_attention_view(groups, preferences=collapsed)],
            [True, False],
        )

    def test_attention_preferences_do_not_leak_between_motorcycles(self):
        groups = grouped_actions(
            [
                MaintenanceItem("Engine oil", interval_km=4000, last_service_odometer_km=14000),
                MaintenanceItem("Chain inspection", interval_km=3000, last_service_odometer_km=15420),
            ],
            MotorcycleState(date(2026, 7, 31), 18420),
        )
        preferences = toggle_group(AttentionViewPreferences("moto-1"), "due")
        self.assertEqual(
            [group.expanded for group in build_attention_view(groups, preferences=preferences, scope_id="moto-1")],
            [True, True],
        )
        self.assertEqual(
            [group.expanded for group in build_attention_view(groups, preferences=preferences, scope_id="moto-2")],
            [True, False],
        )

    def test_attention_preferences_sync_uses_revision_and_device_tie_breaker(self):
        local = snapshot_preferences(
            AttentionViewPreferences("moto-1", frozenset({"due"})),
            owner_id="owner-1",
            revision=2,
            device_id="phone",
        )
        remote = snapshot_preferences(
            AttentionViewPreferences("moto-1", frozenset({"due", "approaching_due"})),
            owner_id="owner-1",
            revision=3,
            device_id="web",
        )
        merged = merge_preference_snapshots(local, remote)
        self.assertEqual(merged.device_id, "web")
        self.assertEqual(
            preferences_from_snapshot(merged).expanded_statuses,
            frozenset({"due", "approaching_due"}),
        )

    def test_attention_preference_sync_tie_breaks_deterministically(self):
        first = snapshot_preferences(AttentionViewPreferences("moto-1"), owner_id="owner-1", revision=4, device_id="phone")
        second = snapshot_preferences(
            AttentionViewPreferences("moto-1", frozenset({"due"})), owner_id="owner-1", revision=4, device_id="web"
        )
        self.assertEqual(merge_preference_snapshots(first, second).device_id, "web")

    def test_attention_preference_sync_rejects_different_motorcycles(self):
        first = snapshot_preferences(AttentionViewPreferences("moto-1"), owner_id="owner-1", revision=1, device_id="phone")
        second = snapshot_preferences(AttentionViewPreferences("moto-2"), owner_id="owner-1", revision=1, device_id="phone")
        with self.assertRaises(ValueError):
            merge_preference_snapshots(first, second)

    def test_attention_preference_sync_rejects_different_owners(self):
        first = snapshot_preferences(AttentionViewPreferences("moto-1"), owner_id="owner-1", revision=1, device_id="phone")
        second = snapshot_preferences(AttentionViewPreferences("moto-1"), owner_id="owner-2", revision=2, device_id="web")
        with self.assertRaises(ValueError):
            merge_preference_snapshots(first, second)

    def test_owner_can_sync_preferences_and_higher_revision_wins(self):
        stored = snapshot_preferences(
            AttentionViewPreferences("moto-1", frozenset({"due"})),
            owner_id="owner-1",
            revision=2,
            device_id="phone",
        )
        incoming = snapshot_preferences(
            AttentionViewPreferences("moto-1", frozenset({"due", "approaching_due"})),
            owner_id="owner-1",
            revision=3,
            device_id="web",
        )
        state, response = handle_preference_sync(
            AttentionSyncState("owner-1", (stored,)), "owner-1", incoming
        )
        self.assertTrue(response.accepted)
        self.assertEqual(response.code, "preference_sync_accepted")
        self.assertEqual(state.snapshots, (incoming,))

    def test_non_owner_sync_is_rejected_without_state_mutation(self):
        incoming = snapshot_preferences(
            AttentionViewPreferences("moto-1"), owner_id="owner-1", revision=1, device_id="phone"
        )
        state = AttentionSyncState("owner-1")
        updated, response = handle_preference_sync(state, "owner-2", incoming)
        self.assertFalse(response.accepted)
        self.assertEqual(response.code, "preference_sync_forbidden")
        self.assertEqual(updated, state)

    def test_account_preference_store_is_owner_and_motorcycle_scoped(self):
        store = InMemoryAttentionPreferenceStore()
        first = snapshot_preferences(
            AttentionViewPreferences("moto-1", frozenset({"due"})),
            owner_id="owner-1",
            revision=2,
            device_id="phone",
        )
        stale = snapshot_preferences(
            AttentionViewPreferences("moto-1", frozenset()),
            owner_id="owner-1",
            revision=1,
            device_id="web",
        )
        other_motorcycle = snapshot_preferences(
            AttentionViewPreferences("moto-2", frozenset({"overdue"})),
            owner_id="owner-1",
            revision=1,
            device_id="phone",
        )
        self.assertEqual(store.save(first), first)
        self.assertEqual(store.save(stale), first)
        self.assertEqual(store.save(other_motorcycle), other_motorcycle)
        self.assertEqual(store.load("owner-1", "moto-1"), first)
        self.assertIsNone(store.load("owner-2", "moto-1"))

    def test_preference_snapshot_requires_non_empty_motorcycle_scope(self):
        with self.assertRaises(ValueError):
            snapshot_preferences(
                AttentionViewPreferences(),
                owner_id="owner-1",
                revision=1,
                device_id="phone",
            )

    def test_owner_status_combines_maintenance_and_document_attention(self):
        view = build_owner_status(
            "moto-1",
            MotorcycleState(date(2026, 7, 31), 18420),
            [
                MaintenanceItem(
                    "Chain inspection",
                    interval_km=3000,
                    warning_km=500,
                    last_service_odometer_km=15900,
                )
            ],
            [DocumentObligation("Licensing renewal", date(2026, 8, 24), warning_days=30)],
        )
        self.assertEqual([item.source for item in view.attention], ["maintenance", "document"])
        self.assertEqual(view.next_action_titles, ("Chain inspection", "Licensing renewal"))

    def test_owner_status_prioritizes_overdue_and_keeps_unknown_visible(self):
        view = build_owner_status(
            "moto-1",
            MotorcycleState(date(2026, 7, 31), 18420, date(2026, 1, 1)),
            [
                MaintenanceItem(
                    "Tire inspection",
                    interval_days=30,
                    last_service_date=date(2026, 6, 1),
                ),
                MaintenanceItem("Chain inspection", interval_km=3000, last_service_odometer_km=15900),
            ],
            [],
        )
        self.assertEqual(view.attention[0].status, MaintenanceStatus.OVERDUE)
        self.assertEqual(view.attention[1].status, MaintenanceStatus.UNKNOWN)
        self.assertEqual(view.next_action_titles, ("Tire inspection",))

    def test_owner_status_preserves_odometer_metadata(self):
        recorded = date(2026, 7, 30)
        view = build_owner_status("moto-1", MotorcycleState(date(2026, 7, 31), 18420, recorded), [], [])
        self.assertEqual(view.odometer_km, 18420)
        self.assertEqual(view.odometer_recorded_at, recorded)

    def test_owner_status_exposes_configurable_odometer_freshness(self):
        view = build_owner_status(
            "moto-1",
            MotorcycleState(date(2026, 7, 31), 18420, date(2026, 7, 1)),
            [MaintenanceItem("Chain inspection", interval_km=3000, last_service_odometer_km=15900)],
            [],
            odometer_stale_after_days=29,
        )
        self.assertEqual(view.attention[0].status, MaintenanceStatus.UNKNOWN)
        self.assertEqual(view.next_action_titles, ())

    def test_owner_status_payload_is_snake_case_and_json_ready(self):
        view = build_owner_status(
            "moto-1",
            MotorcycleState(date(2026, 7, 31), 18420, date(2026, 7, 30)),
            [
                MaintenanceItem(
                    "Chain inspection",
                    interval_km=3000,
                    warning_km=500,
                    last_service_odometer_km=15900,
                )
            ],
            [DocumentObligation("Licensing renewal", date(2026, 8, 24), warning_days=30)],
        )
        payload = owner_status_payload(view, odometer_stale_after_days=45)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["motorcycle_id"], "moto-1")
        self.assertEqual(payload["current_odometer_km"], 18420)
        self.assertEqual(payload["odometer_recorded_at"], "2026-07-30")
        self.assertEqual(payload["odometer_stale_after_days"], 45)
        self.assertEqual(payload["attention"][0]["status"], "approaching_due")
        self.assertEqual(payload["next_action_titles"], ["Chain inspection", "Licensing renewal"])

    def test_owner_status_api_contract_returns_versioned_private_response(self):
        response = get_owner_status_response(
            actor_id="owner-1",
            owner_id="owner-1",
            motorcycle_id="moto-1",
            motorcycle=MotorcycleState(date(2026, 7, 31), 18420),
            maintenance_items=[],
            obligations=[],
        )
        self.assertEqual(OWNER_STATUS_ROUTE, "/api/v1/motorcycles/{motorcycle_id}/maintenance-status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["schema_version"], 1)
        self.assertEqual(response.body["motorcycle_id"], "moto-1")

    def test_owner_status_api_rejects_non_owner_without_data(self):
        response = get_owner_status_response(
            actor_id="other-user",
            owner_id="owner-1",
            motorcycle_id="moto-1",
            motorcycle=MotorcycleState(date(2026, 7, 31), 18420),
            maintenance_items=[],
            obligations=[],
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.body["schema_version"], 1)
        self.assertEqual(response.body["code"], "motorcycle_status_forbidden")
        self.assertNotIn("attention", response.body)

    def test_service_history_api_returns_active_records_for_owner(self):
        record = ServiceRecorded(date(2026, 7, 1), 18000, ("oil",), service_id="service-1")
        response = get_service_history_response(
            actor_id="owner-1",
            state=ServiceHistoryState("moto-1", "owner-1", records=(record,)),
        )
        self.assertEqual(SERVICE_HISTORY_ROUTE, "/api/v1/motorcycles/{motorcycle_id}/service-history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["records"][0]["service_id"], "service-1")

    def test_service_history_api_rejects_non_owner_without_records(self):
        record = ServiceRecorded(date(2026, 7, 1), 18000, ("oil",), service_id="service-1")
        response = get_service_history_response(
            actor_id="mechanic-1",
            state=ServiceHistoryState("moto-1", "owner-1", records=(record,)),
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("records", response.body)

    def test_odometer_history_accepts_monotonic_readings(self):
        history, first = record_odometer_reading(
            OdometerHistory(), "reading-1", 18000, date(2026, 7, 1)
        )
        history, second = record_odometer_reading(
            history, "reading-2", 18420, date(2026, 7, 31)
        )
        self.assertEqual(first.value_km, 18000)
        self.assertEqual(current_odometer_reading(history), second)

    def test_odometer_history_rejects_normal_decrease(self):
        history, _ = record_odometer_reading(
            OdometerHistory(), "reading-1", 18000, date(2026, 7, 1)
        )
        with self.assertRaises(ValueError):
            record_odometer_reading(history, "reading-2", 17900, date(2026, 7, 31))

    def test_odometer_correction_preserves_history_and_changes_projection(self):
        history, original = record_odometer_reading(
            OdometerHistory(), "reading-1", 18000, date(2026, 7, 1)
        )
        history, correction = record_odometer_reading(
            history,
            "correction-1",
            17500,
            date(2026, 7, 2),
            correction_of=original.reading_id,
            note="Dashboard typo",
        )
        self.assertEqual(len(history.readings), 2)
        self.assertEqual(current_odometer_reading(history), correction)
        self.assertEqual(correction.correction_of, "reading-1")

    def test_odometer_correction_requires_existing_uncorrected_reading(self):
        with self.assertRaises(ValueError):
            record_odometer_reading(
                OdometerHistory(),
                "correction-1",
                17500,
                date(2026, 7, 2),
                correction_of="missing",
            )

    def test_next_action_keeps_first_grouped_action_compatibility(self):
        items = [
            MaintenanceItem(
                interval_days=30,
                warning_days=7,
                last_service_date=date(2026, 7, 8),
                title="Brake inspection",
            ),
            MaintenanceItem(
                interval_km=3000,
                warning_km=500,
                last_service_odometer_km=15900,
                title="Chain inspection",
            ),
        ]
        self.assertEqual(
            next_action(items, MotorcycleState(date(2026, 7, 31), 18420)).title,
            "Brake inspection",
        )

    def test_service_completion_resets_only_completed_item_baseline(self):
        original = MaintenanceItem(
            interval_km=3000,
            interval_days=90,
            warning_km=500,
            warning_days=14,
            last_service_odometer_km=15000,
            last_service_date=date(2026, 5, 1),
            title="chain",
        )
        updated, event = complete_service(original, date(2026, 7, 31), 18420)
        self.assertEqual(event.maintenance_title, "chain")
        self.assertEqual(updated.last_service_odometer_km, 18420)
        self.assertEqual(updated.last_service_date, date(2026, 7, 31))
        self.assertEqual(
            assess(updated, MotorcycleState(date(2026, 7, 31), 18420)).status,
            MaintenanceStatus.OK,
        )
        self.assertEqual(original.last_service_odometer_km, 15000)

    def test_service_record_updates_only_selected_items_and_is_auditable(self):
        items = [
            MaintenanceItem(
                "Engine oil",
                interval_km=4000,
                last_service_odometer_km=14000,
            ),
            MaintenanceItem(
                "Chain inspection",
                interval_km=3000,
                last_service_odometer_km=15900,
            ),
        ]
        updated, event = record_service(
            items,
            ["Chain inspection"],
            date(2026, 7, 31),
            18420,
            provider_name="Local mechanic",
            notes="Chain adjusted",
        )
        self.assertEqual(event.completed_titles, ("Chain inspection",))
        self.assertEqual(event.provider_name, "Local mechanic")
        self.assertEqual(updated[0].last_service_odometer_km, 14000)
        self.assertEqual(updated[1].last_service_odometer_km, 18420)
        self.assertEqual(
            assess(updated[0], MotorcycleState(date(2026, 7, 31), 18420)).status,
            MaintenanceStatus.OVERDUE,
        )
        self.assertEqual(
            assess(updated[1], MotorcycleState(date(2026, 7, 31), 18420)).status,
            MaintenanceStatus.OK,
        )

    def test_service_record_rejects_duplicate_or_unknown_items(self):
        item = MaintenanceItem("Engine oil")
        with self.assertRaises(ValueError):
            record_service([item], ["Engine oil", "Engine oil"], date(2026, 7, 31), 18000)
        with self.assertRaises(ValueError):
            record_service([item], ["Chain inspection"], date(2026, 7, 31), 18000)

    def test_voided_later_service_projects_the_prior_active_baseline(self):
        item = MaintenanceItem(
            "Chain inspection",
            interval_km=3000,
            last_service_odometer_km=15000,
        )
        _, first = record_service(
            [item], ["Chain inspection"], date(2026, 7, 1), 18000, service_id="service-a"
        )
        _, correction = record_service(
            [item], ["Chain inspection"], date(2026, 7, 15), 19000, service_id="service-b"
        )
        voided = void_service_record("service-b", "Incorrect odometer")
        projected = project_service_history([item], [first, correction], [voided])
        self.assertEqual(projected[0].last_service_odometer_km, 18000)
        self.assertEqual(
            assess(projected[0], MotorcycleState(date(2026, 7, 31), 18420)).remaining_km,
            2580,
        )

    def test_void_record_requires_id_and_reason(self):
        with self.assertRaises(ValueError):
            void_service_record("", "reason")
        with self.assertRaises(ValueError):
            void_service_record("service-a", "")

    def test_owner_can_void_service_record_and_event_is_preserved(self):
        item = MaintenanceItem("Chain inspection")
        _, record = record_service(
            [item], ["Chain inspection"], date(2026, 7, 31), 18420, service_id="service-a"
        )
        state = ServiceHistoryState("moto-1", "owner-1", records=(record,))
        updated, event = void_service_record_for_owner(
            state, "owner-1", "service-a", "Incorrect odometer"
        )
        self.assertEqual(event.service_id, "service-a")
        self.assertEqual(updated.records, (record,))
        self.assertEqual(updated.voided_records, (event,))

    def test_non_owner_cannot_void_service_record(self):
        item = MaintenanceItem("Chain inspection")
        _, record = record_service(
            [item], ["Chain inspection"], date(2026, 7, 31), 18420, service_id="service-a"
        )
        state = ServiceHistoryState("moto-1", "owner-1", records=(record,))
        with self.assertRaises(PermissionError):
            void_service_record_for_owner(state, "mechanic-1", "service-a", "Correction")

    def test_unknown_or_already_voided_record_has_explicit_error(self):
        state = ServiceHistoryState("moto-1", "owner-1")
        with self.assertRaises(LookupError):
            void_service_record_for_owner(state, "owner-1", "missing", "Correction")
        item = MaintenanceItem("Chain inspection")
        _, record = record_service(
            [item], ["Chain inspection"], date(2026, 7, 31), 18420, service_id="service-a"
        )
        state = ServiceHistoryState("moto-1", "owner-1", records=(record,))
        state, _ = void_service_record_for_owner(state, "owner-1", "service-a", "Correction")
        with self.assertRaises(ValueError):
            void_service_record_for_owner(state, "owner-1", "service-a", "Correction again")

    def test_correction_errors_expose_stable_codes_and_safe_messages(self):
        state = ServiceHistoryState("moto-1", "owner-1")
        with self.assertRaises(ServiceCorrectionNotFound) as missing:
            void_service_record_for_owner(state, "owner-1", "missing", "Correction")
        self.assertEqual(missing.exception.code, "service_record_not_found")
        self.assertEqual(str(missing.exception), "This service record is no longer available.")

        item = MaintenanceItem("Chain inspection")
        _, record = record_service(
            [item], ["Chain inspection"], date(2026, 7, 31), 18420, service_id="service-a"
        )
        state = ServiceHistoryState("moto-1", "owner-1", records=(record,))
        with self.assertRaises(ServiceCorrectionForbidden) as forbidden:
            void_service_record_for_owner(state, "mechanic-1", "service-a", "Correction")
        self.assertEqual(forbidden.exception.code, "service_correction_forbidden")

        state, _ = void_service_record_for_owner(state, "owner-1", "service-a", "Correction")
        with self.assertRaises(ServiceCorrectionAlreadyVoided) as repeated:
            void_service_record_for_owner(state, "owner-1", "service-a", "Correction again")
        self.assertEqual(repeated.exception.code, "service_record_already_voided")

    def test_correction_command_returns_framework_neutral_success_response(self):
        item = MaintenanceItem("Chain inspection")
        _, record = record_service(
            [item], ["Chain inspection"], date(2026, 7, 31), 18420, service_id="service-a"
        )
        state = ServiceHistoryState("moto-1", "owner-1", records=(record,))
        updated, response = handle_correction(
            state,
            CorrectionCommand("owner-1", "service-a", "Incorrect odometer"),
        )
        self.assertTrue(response.accepted)
        self.assertEqual(response.code, "service_record_voided")
        self.assertEqual(response.service_id, "service-a")
        self.assertEqual(response.message, "Service record correction recorded.")
        self.assertEqual(len(updated.voided_records), 1)

    def test_correction_command_returns_error_without_mutating_state(self):
        state = ServiceHistoryState("moto-1", "owner-1")
        updated, response = handle_correction(
            state,
            CorrectionCommand("mechanic-1", "missing", "Correction"),
        )
        self.assertFalse(response.accepted)
        self.assertEqual(response.code, "service_correction_forbidden")
        self.assertIsNone(response.service_id)
        self.assertEqual(updated, state)

    def test_service_completion_rejects_negative_odometer(self):
        with self.assertRaises(ValueError):
            complete_service(MaintenanceItem(title="chain"), date(2026, 7, 31), -1)

    def test_document_obligation_approaches_due_by_date(self):
        result = assess_obligation(
            DocumentObligation("Licensing renewal", date(2026, 8, 24), warning_days=30),
            date(2026, 7, 31),
        )
        self.assertEqual(result.status, MaintenanceStatus.APPROACHING_DUE)
        self.assertEqual(result.remaining_days, 24)

    def test_completed_document_obligation_is_not_actionable(self):
        obligation = DocumentObligation(
            "Insurance renewal",
            date(2026, 7, 1),
            completed_at=date(2026, 6, 30),
        )
        self.assertEqual(
            assess_obligation(obligation, date(2026, 7, 31)).status,
            MaintenanceStatus.UNKNOWN,
        )
        self.assertEqual(next_obligation_actions([obligation], date(2026, 7, 31)), [])

    def test_owner_attention_combines_maintenance_and_obligations(self):
        maintenance = [
            MaintenanceItem(
                "Chain inspection",
                interval_km=3000,
                warning_km=500,
                last_service_odometer_km=15900,
            )
        ]
        obligations = [
            DocumentObligation("Licensing renewal", date(2026, 8, 24), warning_days=30)
        ]
        actions = next_owner_actions(
            maintenance,
            obligations,
            MotorcycleState(date(2026, 7, 31), 18420),
        )
        self.assertEqual([action.title for action in actions], ["Chain inspection", "Licensing renewal"])

    def test_daily_commuter_keeps_odometer_fresh(self):
        result = simulate_profile(
            daily_commuter(),
            start_date=date(2026, 1, 1),
            days=365,
            starting_odometer_km=18000,
            item=MaintenanceItem(
                "Engine oil",
                interval_km=4000,
                warning_km=500,
                last_service_odometer_km=18000,
            ),
        )
        self.assertEqual(result.unknown_days, 0)
        self.assertGreater(result.attention_days, 0)

    def test_weekend_rider_keeps_odometer_fresh(self):
        result = simulate_profile(
            weekend_rider(),
            start_date=date(2026, 1, 1),
            days=365,
            starting_odometer_km=18000,
            item=MaintenanceItem(
                "Engine oil",
                interval_km=4000,
                warning_km=500,
                last_service_odometer_km=18000,
            ),
        )
        self.assertEqual(result.unknown_days, 0)

    def test_long_unused_motorcycle_becomes_unknown_after_freshness_window(self):
        result = simulate_profile(
            long_unused(),
            start_date=date(2026, 1, 1),
            days=365,
            starting_odometer_km=18000,
            item=MaintenanceItem(
                "Engine oil",
                interval_km=4000,
                last_service_odometer_km=18000,
            ),
        )
        self.assertEqual(result.unknown_days, 274)

    def test_reminder_cadence_suppresses_daily_repeat(self):
        tracker = ReminderTracker(ReminderPolicy(repeat_every_days=14))
        assessment = MaintenanceAssessment("Chain inspection", MaintenanceStatus.OVERDUE)
        self.assertEqual(tracker.evaluate(date(2026, 1, 1), [assessment]), ["Chain inspection"])
        self.assertEqual(tracker.evaluate(date(2026, 1, 2), [assessment]), [])
        self.assertEqual(tracker.evaluate(date(2026, 1, 14), [assessment]), [])
        self.assertEqual(tracker.evaluate(date(2026, 1, 15), [assessment]), ["Chain inspection"])

    def test_reminder_escalates_immediately(self):
        tracker = ReminderTracker()
        approaching = MaintenanceAssessment("Chain inspection", MaintenanceStatus.APPROACHING_DUE)
        overdue = MaintenanceAssessment("Chain inspection", MaintenanceStatus.OVERDUE)
        self.assertEqual(tracker.evaluate(date(2026, 1, 1), [approaching]), ["Chain inspection"])
        self.assertEqual(tracker.evaluate(date(2026, 1, 2), [overdue]), ["Chain inspection"])

    def test_ok_and_unknown_do_not_remind_and_clear_cadence(self):
        tracker = ReminderTracker()
        overdue = MaintenanceAssessment("Chain inspection", MaintenanceStatus.OVERDUE)
        ok = MaintenanceAssessment("Chain inspection", MaintenanceStatus.OK)
        unknown = MaintenanceAssessment("Chain inspection", MaintenanceStatus.UNKNOWN)
        self.assertEqual(tracker.evaluate(date(2026, 1, 1), [overdue]), ["Chain inspection"])
        self.assertEqual(tracker.evaluate(date(2026, 1, 2), [ok]), [])
        self.assertEqual(tracker.evaluate(date(2026, 1, 3), [unknown]), [])
        self.assertEqual(tracker.evaluate(date(2026, 1, 4), [overdue]), ["Chain inspection"])

    def test_longer_cadence_reduces_commuter_reminder_volume(self):
        item = MaintenanceItem(
            "Engine oil",
            interval_km=4000,
            warning_km=500,
            last_service_odometer_km=18000,
        )
        results = [
            simulate_profile_reminders(
                daily_commuter(),
                start_date=date(2026, 1, 1),
                days=365,
                starting_odometer_km=18000,
                item=item,
                cadence_days=cadence,
            )
            for cadence in (7, 14, 30)
        ]
        self.assertGreater(results[0].reminder_count, results[1].reminder_count)
        self.assertGreater(results[1].reminder_count, results[2].reminder_count)

    def test_unused_profile_stops_reminding_when_status_becomes_unknown(self):
        result = simulate_profile_reminders(
            long_unused(),
            start_date=date(2026, 1, 1),
            days=365,
            starting_odometer_km=18000,
            item=MaintenanceItem(
                "Engine oil",
                interval_km=4000,
                last_service_odometer_km=18000,
            ),
            cadence_days=14,
        )
        self.assertEqual(result.unknown_days, 274)
        self.assertEqual(result.reminder_count, 0)


if __name__ == "__main__":
    unittest.main()
