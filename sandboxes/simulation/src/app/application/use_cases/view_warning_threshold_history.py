from __future__ import annotations

from dataclasses import dataclass

from app.domain.maintenance import (
    MaintenanceItem,
    WarningThresholdEvent,
    project_warning_threshold_history,
)


@dataclass(frozen=True)
class WarningThresholdHistoryView:
    effective_item: MaintenanceItem
    events: tuple[WarningThresholdEvent, ...]


class WarningThresholdHistoryViewForbidden(PermissionError):
    """Raised when a non-owner requests threshold history."""

    code = "warning_threshold_history_forbidden"
    user_message = "Only the motorcycle owner can view warning threshold history."

    def __init__(self) -> None:
        super().__init__(self.user_message)


class ViewWarningThresholdHistory:
    """Query the effective policy and audit events for one item."""

    def execute(
        self,
        item: MaintenanceItem,
        events: list[WarningThresholdEvent],
        *,
        actor_id: str,
        owner_id: str,
    ) -> WarningThresholdHistoryView:
        if actor_id != owner_id:
            raise WarningThresholdHistoryViewForbidden()
        return WarningThresholdHistoryView(
            effective_item=project_warning_threshold_history(item, events),
            events=tuple(events),
        )
