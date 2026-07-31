from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.maintenance import (
    MaintenanceAssessment,
    MaintenanceItem,
    MaintenanceStatus,
    MotorcycleState,
    next_actions,
)


@dataclass(frozen=True)
class DocumentObligation:
    title: str
    due_date: date
    warning_days: int = 30
    completed_at: date | None = None
    enabled: bool = True


def assess_obligation(
    obligation: DocumentObligation, current_date: date
) -> MaintenanceAssessment:
    if not obligation.enabled or obligation.completed_at is not None:
        return MaintenanceAssessment(obligation.title, MaintenanceStatus.UNKNOWN)

    remaining_days = (obligation.due_date - current_date).days
    if remaining_days < 0:
        status = MaintenanceStatus.OVERDUE
    elif remaining_days == 0:
        status = MaintenanceStatus.DUE
    elif remaining_days <= obligation.warning_days:
        status = MaintenanceStatus.APPROACHING_DUE
    else:
        status = MaintenanceStatus.OK
    return MaintenanceAssessment(obligation.title, status, remaining_days=remaining_days)


def next_obligation_actions(
    obligations: list[DocumentObligation], current_date: date
) -> list[MaintenanceAssessment]:
    assessments = [
        assess_obligation(obligation, current_date)
        for obligation in obligations
        if obligation.enabled and obligation.completed_at is None
    ]
    actionable = [
        assessment
        for assessment in assessments
        if assessment.status
        in {
            MaintenanceStatus.OVERDUE,
            MaintenanceStatus.DUE,
            MaintenanceStatus.APPROACHING_DUE,
        }
    ]
    if not actionable:
        return []
    urgency = {
        MaintenanceStatus.OVERDUE: 0,
        MaintenanceStatus.DUE: 1,
        MaintenanceStatus.APPROACHING_DUE: 2,
    }
    highest = min(urgency[item.status] for item in actionable)
    return sorted(
        [item for item in actionable if urgency[item.status] == highest],
        key=lambda item: item.title,
    )


def next_owner_actions(
    maintenance_items: list[MaintenanceItem],
    obligations: list[DocumentObligation],
    motorcycle: MotorcycleState,
) -> list[MaintenanceAssessment]:
    """Combine mechanical and legal attention without changing either model."""
    actions = next_actions(maintenance_items, motorcycle)
    actions.extend(next_obligation_actions(obligations, motorcycle.current_date))
    if not actions:
        return []
    urgency = {
        MaintenanceStatus.OVERDUE: 0,
        MaintenanceStatus.DUE: 1,
        MaintenanceStatus.APPROACHING_DUE: 2,
    }
    highest = min(urgency[item.status] for item in actions)
    return sorted(
        [item for item in actions if urgency[item.status] == highest],
        key=lambda item: item.title,
    )
