from __future__ import annotations

from app.application.owner_status_api import ApiResponse
from app.application.owner_status_payload import OWNER_STATUS_SCHEMA_VERSION
from app.application.service_history import ServiceHistoryState, ServiceHistoryViewForbidden
from app.application.use_cases.view_service_history import ViewServiceHistory


SERVICE_HISTORY_ROUTE = "/api/v1/motorcycles/{motorcycle_id}/service-history"


def get_service_history_response(
    *, actor_id: str, state: ServiceHistoryState
) -> ApiResponse:
    """Framework-neutral private API response for active service history."""
    try:
        records = ViewServiceHistory().execute(state, actor_id=actor_id)
    except ServiceHistoryViewForbidden as error:
        return ApiResponse(
            403,
            {
                "schema_version": OWNER_STATUS_SCHEMA_VERSION,
                "code": error.code,
                "message": str(error),
            },
        )
    return ApiResponse(
        200,
        {
            "schema_version": OWNER_STATUS_SCHEMA_VERSION,
            "motorcycle_id": state.motorcycle_id,
            "records": [
                {
                    "service_id": record.service_id,
                    "serviced_at": record.serviced_at.isoformat(),
                    "odometer_km": record.odometer_km,
                    "completed_titles": list(record.completed_titles),
                    "provider_name": record.provider_name,
                    "notes": record.notes,
                }
                for record in records
            ],
        },
    )
