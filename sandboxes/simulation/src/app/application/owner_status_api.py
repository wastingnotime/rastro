from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.owner_dashboard import build_owner_status
from app.application.owner_status_payload import owner_status_payload
from app.domain.maintenance import MaintenanceItem, MotorcycleState
from app.domain.obligations import DocumentObligation


OWNER_STATUS_ROUTE = "/api/v1/motorcycles/{motorcycle_id}/maintenance-status"


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    body: dict[str, Any]


def get_owner_status_response(
    *,
    actor_id: str,
    owner_id: str,
    motorcycle_id: str,
    motorcycle: MotorcycleState,
    maintenance_items: list[MaintenanceItem],
    obligations: list[DocumentObligation],
    odometer_stale_after_days: int = 90,
) -> ApiResponse:
    """Framework-neutral private API response for the owner status query."""
    if actor_id != owner_id:
        return ApiResponse(
            403,
            {
                "code": "motorcycle_status_forbidden",
                "message": "Only the motorcycle owner can view maintenance status.",
            },
        )
    view = build_owner_status(
        motorcycle_id,
        motorcycle,
        maintenance_items,
        obligations,
        odometer_stale_after_days=odometer_stale_after_days,
    )
    return ApiResponse(200, owner_status_payload(view, odometer_stale_after_days=odometer_stale_after_days))
