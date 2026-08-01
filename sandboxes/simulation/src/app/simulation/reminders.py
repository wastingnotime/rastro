from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.maintenance import MaintenanceAssessment, MaintenanceStatus


@dataclass(frozen=True)
class ReminderPolicy:
    repeat_every_days: int = 14

    def __post_init__(self) -> None:
        if self.repeat_every_days < 1:
            raise ValueError("reminder cadence must be at least one day")


class ReminderTracker:
    """Stateful simulation policy for reducing repeated owner reminders."""

    def __init__(self, policy: ReminderPolicy = ReminderPolicy()) -> None:
        self.policy = policy
        self._last_status: dict[str, MaintenanceStatus] = {}
        self._last_reminded: dict[str, date] = {}

    def evaluate(
        self, current_date: date, assessments: list[MaintenanceAssessment]
    ) -> list[str]:
        reminders: list[str] = []
        for assessment in assessments:
            previous = self._last_status.get(assessment.title)
            self._last_status[assessment.title] = assessment.status
            if assessment.status not in {
                MaintenanceStatus.OVERDUE,
                MaintenanceStatus.DUE,
                MaintenanceStatus.APPROACHING_DUE,
            }:
                self._last_reminded.pop(assessment.title, None)
                continue

            last_reminded = self._last_reminded.get(assessment.title)
            escalated = previous is not None and _urgency(assessment.status) < _urgency(previous)
            due_for_repeat = (
                last_reminded is not None
                and (current_date - last_reminded).days >= self.policy.repeat_every_days
            )
            if last_reminded is None or escalated or due_for_repeat:
                reminders.append(assessment.title)
                self._last_reminded[assessment.title] = current_date
        return reminders


def _urgency(status: MaintenanceStatus) -> int:
    return {
        MaintenanceStatus.OVERDUE: 0,
        MaintenanceStatus.DUE: 1,
        MaintenanceStatus.APPROACHING_DUE: 2,
        MaintenanceStatus.OK: 3,
        MaintenanceStatus.UNKNOWN: 4,
    }[status]
