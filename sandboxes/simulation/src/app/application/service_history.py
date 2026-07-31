from __future__ import annotations

from dataclasses import dataclass

from app.domain.maintenance import ServiceRecorded, ServiceRecordVoided, void_service_record


@dataclass(frozen=True)
class ServiceHistoryState:
    motorcycle_id: str
    owner_id: str
    records: tuple[ServiceRecorded, ...] = ()
    voided_records: tuple[ServiceRecordVoided, ...] = ()


class ServiceCorrectionError(Exception):
    code = "service_correction_failed"
    user_message = "The service history could not be corrected."

    def __init__(self) -> None:
        super().__init__(self.user_message)


class ServiceCorrectionForbidden(ServiceCorrectionError, PermissionError):
    code = "service_correction_forbidden"
    user_message = "Only the motorcycle owner can correct service history."


class ServiceCorrectionNotFound(ServiceCorrectionError, LookupError):
    code = "service_record_not_found"
    user_message = "This service record is no longer available."


class ServiceCorrectionAlreadyVoided(ServiceCorrectionError, ValueError):
    code = "service_record_already_voided"
    user_message = "This service record has already been corrected."


def void_service_record_for_owner(
    state: ServiceHistoryState,
    actor_id: str,
    service_id: str,
    reason: str,
) -> tuple[ServiceHistoryState, ServiceRecordVoided]:
    """Authorize a correction while preserving the append-only domain event."""
    if actor_id != state.owner_id:
        raise ServiceCorrectionForbidden()
    if not any(record.service_id == service_id for record in state.records):
        raise ServiceCorrectionNotFound()
    if any(event.service_id == service_id for event in state.voided_records):
        raise ServiceCorrectionAlreadyVoided()
    event = void_service_record(service_id, reason)
    updated = ServiceHistoryState(
        motorcycle_id=state.motorcycle_id,
        owner_id=state.owner_id,
        records=state.records,
        voided_records=state.voided_records + (event,),
    )
    return updated, event
