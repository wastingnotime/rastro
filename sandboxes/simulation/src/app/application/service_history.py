from __future__ import annotations

from dataclasses import dataclass

from app.domain.maintenance import ServiceRecorded, ServiceRecordVoided, void_service_record


@dataclass(frozen=True)
class ServiceHistoryState:
    motorcycle_id: str
    owner_id: str
    records: tuple[ServiceRecorded, ...] = ()
    voided_records: tuple[ServiceRecordVoided, ...] = ()


def void_service_record_for_owner(
    state: ServiceHistoryState,
    actor_id: str,
    service_id: str,
    reason: str,
) -> tuple[ServiceHistoryState, ServiceRecordVoided]:
    """Authorize a correction while preserving the append-only domain event."""
    if actor_id != state.owner_id:
        raise PermissionError("only the motorcycle owner can correct service history")
    if not any(record.service_id == service_id for record in state.records):
        raise LookupError("service record was not found for this motorcycle")
    if any(event.service_id == service_id for event in state.voided_records):
        raise ValueError("service record is already voided")
    event = void_service_record(service_id, reason)
    updated = ServiceHistoryState(
        motorcycle_id=state.motorcycle_id,
        owner_id=state.owner_id,
        records=state.records,
        voided_records=state.voided_records + (event,),
    )
    return updated, event
