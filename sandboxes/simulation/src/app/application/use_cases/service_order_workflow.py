from __future__ import annotations

from datetime import date

from app.domain.maintenance import MaintenanceItem, ServiceRecorded, record_service
from app.domain.service_order import MotorcycleIdentity, ServiceOrder


class IdentifyMotorcycle:
    def execute(self, **identity: object) -> MotorcycleIdentity:
        return MotorcycleIdentity(**identity)  # type: ignore[arg-type]


class CreateServiceRequest:
    def execute(self, **request: object) -> ServiceOrder:
        return ServiceOrder.request(**request)  # type: ignore[arg-type]


class ReviewServiceRequest:
    def execute(self, order: ServiceOrder, **review: object) -> ServiceOrder:
        return order.review(**review)  # type: ignore[arg-type]


class ProposeServiceWork:
    def execute(self, order: ServiceOrder, **proposal: object) -> ServiceOrder:
        return order.propose(**proposal)  # type: ignore[arg-type]


class RespondToServiceProposal:
    def execute(self, order: ServiceOrder, **response: object) -> ServiceOrder:
        return order.respond_to_proposal(**response)  # type: ignore[arg-type]


class StartServiceJob:
    def execute(self, order: ServiceOrder, *, actor_id: str) -> ServiceOrder:
        return order.start(actor_id=actor_id)


class CompleteServiceJob:
    def execute(
        self,
        order: ServiceOrder,
        items: list[MaintenanceItem],
        *,
        actor_id: str,
        completion_notes: str,
        serviced_at: date,
        odometer_km: int,
    ) -> tuple[ServiceOrder, list[MaintenanceItem], ServiceRecorded]:
        completed = order.complete(actor_id=actor_id, completion_notes=completion_notes)
        updated, service_event = record_service(
            items,
            list(order.maintenance_needs),
            serviced_at,
            odometer_km,
            provider_name=actor_id,
            notes=completion_notes,
            service_id=order.order_id,
        )
        return completed, updated, service_event


class IssueServiceInvoice:
    def execute(self, order: ServiceOrder, *, actor_id: str) -> ServiceOrder:
        return order.issue_invoice(actor_id=actor_id)


class PayServiceJob:
    def execute(
        self,
        order: ServiceOrder,
        *,
        actor_id: str,
        amount_cents: int,
        payment_reference: str,
    ) -> ServiceOrder:
        return order.pay(
            actor_id=actor_id,
            amount_cents=amount_cents,
            payment_reference=payment_reference,
        )
