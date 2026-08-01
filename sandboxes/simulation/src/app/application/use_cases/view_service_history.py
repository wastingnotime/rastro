from __future__ import annotations

from app.application.service_history import (
    ServiceHistoryState,
    ServiceHistoryViewForbidden,
)
from app.domain.maintenance import ServiceRecorded


class ViewServiceHistory:
    """Owner query for active, append-only service records."""

    def execute(
        self,
        state: ServiceHistoryState,
        *,
        actor_id: str,
    ) -> tuple[ServiceRecorded, ...]:
        if actor_id != state.owner_id:
            raise ServiceHistoryViewForbidden()
        voided_ids = {event.service_id for event in state.voided_records}
        return tuple(
            record for record in state.records if record.service_id not in voided_ids
        )
