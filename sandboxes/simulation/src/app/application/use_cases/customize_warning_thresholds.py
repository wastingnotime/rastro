from __future__ import annotations

from app.domain.maintenance import (
    MaintenanceItem,
    WarningThresholdsCustomized,
    customize_warning_thresholds_with_event,
)


class CustomizeWarningThresholds:
    """Owner command for changing warning thresholds with an audit event."""

    def execute(
        self,
        item: MaintenanceItem,
        *,
        warning_km: int | None = None,
        warning_days: int | None = None,
    ) -> tuple[MaintenanceItem, WarningThresholdsCustomized]:
        return customize_warning_thresholds_with_event(
            item,
            warning_km=warning_km,
            warning_days=warning_days,
        )
