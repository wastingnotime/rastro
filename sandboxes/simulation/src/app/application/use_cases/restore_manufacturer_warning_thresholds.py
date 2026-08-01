from __future__ import annotations

from app.domain.maintenance import (
    MaintenanceItem,
    WarningThresholdsRestored,
    restore_manufacturer_warning_thresholds_with_event,
)


class RestoreManufacturerWarningThresholds:
    """Owner command for restoring canonical warning thresholds."""

    def execute(
        self,
        item: MaintenanceItem,
        *,
        warning_km: int | None = None,
        warning_days: int | None = None,
    ) -> tuple[MaintenanceItem, WarningThresholdsRestored]:
        return restore_manufacturer_warning_thresholds_with_event(
            item,
            warning_km=warning_km,
            warning_days=warning_days,
        )
