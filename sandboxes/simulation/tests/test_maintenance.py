import unittest
from datetime import date

from app.domain.maintenance import (
    MaintenanceItem,
    MaintenanceStatus,
    MotorcycleState,
    assess,
    complete_service,
    next_action,
    next_actions,
)
from app.domain.obligations import (
    DocumentObligation,
    assess_obligation,
    next_obligation_actions,
    next_owner_actions,
)


class MaintenanceStatusTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
