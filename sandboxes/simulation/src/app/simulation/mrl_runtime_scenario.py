from __future__ import annotations

from datetime import date, datetime, timezone

from mrl_simulation_runtime.actors import Actor
from mrl_simulation_runtime.invariants import Invariant
from mrl_simulation_runtime.scenario import ObservatoryEdge, ObservatoryNode, Scenario

from app.domain.maintenance import (
    MaintenanceItem,
    MotorcycleState,
    MaintenanceStatus,
    assess,
    complete_service,
    next_action,
    next_actions,
)
from app.domain.obligations import DocumentObligation, next_owner_actions


def _start_owner(context: object) -> None:
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
    serviced_chain, event = complete_service(items[1], date(2026, 7, 31), 18420)
    context.emit(
        "domain_event",
        "service_completed",
        source="maintenance-status",
        actor="owner",
        payload={
            "maintenance_item": event.maintenance_title,
            "serviced_at": event.serviced_at.isoformat(),
            "odometer_km": event.odometer_km,
        },
    )
    after_service = assess(serviced_chain, motorcycle)
    context.emit(
        "maintenance_status",
        after_service.title,
        source="maintenance-status",
        actor="owner",
        payload={"status": after_service.status.value, "remaining_km": after_service.remaining_km},
    )


class OwnerBehavior:
    def on_start(self, context: object) -> None:
        _start_owner(context)


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
        ],
        observatory_nodes=[
            ObservatoryNode("owner", "Motorcycle owner", "actor", "domain"),
            ObservatoryNode("status", "Maintenance status", "domain", "domain"),
            ObservatoryNode("action", "Next action", "projection", "application"),
        ],
        observatory_edges=[
            ObservatoryEdge("owner", "status", "checks"),
            ObservatoryEdge("status", "action", "prioritizes"),
        ],
    )
