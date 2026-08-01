from __future__ import annotations

from app.application.owner_dashboard import OwnerStatusView, build_owner_status
from app.domain.maintenance import MaintenanceItem, MotorcycleState
from app.domain.obligations import DocumentObligation


class ViewOwnerStatus:
    """Owner query for the combined maintenance and document attention view."""

    def execute(
        self,
        *,
        motorcycle_id: str,
        motorcycle: MotorcycleState,
        maintenance_items: list[MaintenanceItem],
        obligations: list[DocumentObligation],
        odometer_stale_after_days: int = 90,
    ) -> OwnerStatusView:
        return build_owner_status(
            motorcycle_id,
            motorcycle,
            maintenance_items,
            obligations,
            odometer_stale_after_days=odometer_stale_after_days,
        )
