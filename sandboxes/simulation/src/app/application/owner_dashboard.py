from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.maintenance import (
    MaintenanceAssessment,
    MaintenanceItem,
    MaintenanceStatus,
    MotorcycleState,
    assess,
)
from app.domain.obligations import DocumentObligation, assess_obligation


@dataclass(frozen=True)
class OwnerAttentionItem:
    title: str
    source: str
    status: MaintenanceStatus
    remaining_km: int | None = None
    remaining_days: int | None = None


@dataclass(frozen=True)
class OwnerStatusView:
    motorcycle_id: str
    odometer_km: int | None
    odometer_recorded_at: date | None
    attention: tuple[OwnerAttentionItem, ...]
    next_action_titles: tuple[str, ...]


_URGENCY = {
    MaintenanceStatus.OVERDUE: 0,
    MaintenanceStatus.DUE: 1,
    MaintenanceStatus.APPROACHING_DUE: 2,
    MaintenanceStatus.OK: 3,
    MaintenanceStatus.UNKNOWN: 4,
}


def build_owner_status(
    motorcycle_id: str,
    motorcycle: MotorcycleState,
    maintenance_items: list[MaintenanceItem],
    obligations: list[DocumentObligation],
) -> OwnerStatusView:
    items: list[OwnerAttentionItem] = []
    for maintenance in maintenance_items:
        assessment = assess(maintenance, motorcycle)
        if assessment.status not in {MaintenanceStatus.OK} and maintenance.enabled:
            items.append(_from_assessment(assessment, "maintenance"))
    for obligation in obligations:
        assessment = assess_obligation(obligation, motorcycle.current_date)
        if assessment.status not in {MaintenanceStatus.OK} and obligation.enabled:
            items.append(_from_assessment(assessment, "document"))

    items.sort(key=lambda item: (_URGENCY[item.status], item.title, item.source))
    actionable = [
        item
        for item in items
        if item.status
        in {
            MaintenanceStatus.OVERDUE,
            MaintenanceStatus.DUE,
            MaintenanceStatus.APPROACHING_DUE,
        }
    ]
    next_titles: tuple[str, ...] = ()
    if actionable:
        highest = _URGENCY[actionable[0].status]
        next_titles = tuple(
            item.title for item in actionable if _URGENCY[item.status] == highest
        )
    return OwnerStatusView(
        motorcycle_id=motorcycle_id,
        odometer_km=motorcycle.odometer_km,
        odometer_recorded_at=motorcycle.odometer_recorded_at,
        attention=tuple(items),
        next_action_titles=next_titles,
    )


def _from_assessment(
    assessment: MaintenanceAssessment, source: str
) -> OwnerAttentionItem:
    return OwnerAttentionItem(
        title=assessment.title,
        source=source,
        status=assessment.status,
        remaining_km=assessment.remaining_km,
        remaining_days=assessment.remaining_days,
    )
