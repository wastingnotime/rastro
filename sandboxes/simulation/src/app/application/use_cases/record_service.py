from __future__ import annotations

from datetime import date

from app.domain.maintenance import MaintenanceItem, ServiceRecorded, record_service


class RecordService:
    """Owner command for recording a service visit against selected items."""

    def execute(
        self,
        items: list[MaintenanceItem],
        *,
        completed_titles: list[str],
        serviced_at: date,
        odometer_km: int,
        provider_name: str | None = None,
        notes: str | None = None,
        service_id: str = "service-record",
    ) -> tuple[list[MaintenanceItem], ServiceRecorded]:
        return record_service(
            items,
            completed_titles,
            serviced_at,
            odometer_km,
            provider_name=provider_name,
            notes=notes,
            service_id=service_id,
        )
