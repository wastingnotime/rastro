from __future__ import annotations

from app.application.service_history import (
    CorrectionCommand,
    CorrectionResponse,
    ServiceHistoryState,
    handle_correction,
)


class CorrectServiceRecord:
    """Owner command for correcting a previously recorded service event."""

    def execute(
        self,
        state: ServiceHistoryState,
        *,
        actor_id: str,
        service_id: str,
        reason: str,
    ) -> tuple[ServiceHistoryState, CorrectionResponse]:
        return handle_correction(
            state,
            CorrectionCommand(actor_id, service_id, reason),
        )
