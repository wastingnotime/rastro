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


class ViewWarningThresholdHistory:
    """Query the effective policy and audit events for one item."""

    def execute(
        self,
        item: MaintenanceItem,
        events: list[WarningThresholdEvent],
    ) -> WarningThresholdHistoryView:
        return WarningThresholdHistoryView(
            effective_item=project_warning_threshold_history(item, events),
            events=tuple(events),
        )
