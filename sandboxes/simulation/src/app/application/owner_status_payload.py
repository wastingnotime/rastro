from __future__ import annotations

from typing import Any

from app.application.owner_dashboard import OwnerStatusView


OWNER_STATUS_SCHEMA_VERSION = 1


def owner_status_payload(
    view: OwnerStatusView, *, odometer_stale_after_days: int = 90
) -> dict[str, Any]:
    """Serialize the owner status query into a stable snake_case JSON shape."""
    return {
        "schema_version": OWNER_STATUS_SCHEMA_VERSION,
        "motorcycle_id": view.motorcycle_id,
        "current_odometer_km": view.odometer_km,
        "odometer_recorded_at": (
            view.odometer_recorded_at.isoformat()
            if view.odometer_recorded_at is not None
            else None
        ),
        "odometer_stale_after_days": odometer_stale_after_days,
        "attention": [
            {
                "title": item.title,
                "source": item.source,
                "status": item.status.value,
                "remaining_km": item.remaining_km,
                "remaining_days": item.remaining_days,
            }
            for item in view.attention
        ],
        "next_action_titles": list(view.next_action_titles),
    }
