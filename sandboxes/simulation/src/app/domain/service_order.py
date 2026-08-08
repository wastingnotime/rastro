from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum


class ServiceOrderStatus(str, Enum):
    REQUESTED = "requested"
    UNDER_REVIEW = "under_review"
    PROPOSED = "proposed"
    NEGOTIATING = "negotiating"
    AGREED = "agreed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class MotorcycleIdentity:
    motorcycle_id: str
    owner_id: str
    manufacturer: str
    model: str
    model_year: int
    registration: str | None = None

    def __post_init__(self) -> None:
        for value, message in (
            (self.motorcycle_id, "motorcycle id is required"),
            (self.owner_id, "owner id is required"),
            (self.manufacturer, "motorcycle manufacturer is required"),
            (self.model, "motorcycle model is required"),
        ):
            if not value.strip():
                raise ValueError(message)
        if self.model_year < 1885:
            raise ValueError("motorcycle model year is invalid")


@dataclass(frozen=True)
class ServiceProposal:
    version: int
    work_items: tuple[str, ...]
    parts: tuple[str, ...]
    price_cents: int
    estimated_completion: date
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("proposal version must be positive")
        if not self.work_items or any(not item.strip() for item in self.work_items):
            raise ValueError("proposal work items are required")
        if self.price_cents <= 0:
            raise ValueError("proposal price must be positive")


@dataclass(frozen=True)
class ServiceOrderEvent:
    name: str
    actor_id: str
    details: tuple[tuple[str, object], ...] = ()


@dataclass(frozen=True)
class ServiceOrder:
    order_id: str
    motorcycle: MotorcycleIdentity
    mechanic_id: str
    maintenance_needs: tuple[str, ...]
    maintenance_gaps: tuple[str, ...]
    status: ServiceOrderStatus
    proposals: tuple[ServiceProposal, ...] = ()
    agreed_proposal_version: int | None = None
    invoice_cents: int | None = None
    payment_reference: str | None = None
    events: tuple[ServiceOrderEvent, ...] = ()

    @classmethod
    def request(
        cls,
        *,
        order_id: str,
        motorcycle: MotorcycleIdentity,
        actor_id: str,
        mechanic_id: str,
        maintenance_needs: tuple[str, ...],
        maintenance_gaps: tuple[str, ...] = (),
    ) -> "ServiceOrder":
        if actor_id != motorcycle.owner_id:
            raise PermissionError("only the motorcycle owner can request service")
        if not order_id.strip() or not mechanic_id.strip():
            raise ValueError("order and mechanic ids are required")
        if not maintenance_needs or any(not item.strip() for item in maintenance_needs):
            raise ValueError("at least one maintenance need is required")
        event = ServiceOrderEvent(
            "service_requested",
            actor_id,
            (("mechanic_id", mechanic_id), ("maintenance_needs", maintenance_needs), ("maintenance_gaps", maintenance_gaps)),
        )
        return cls(
            order_id,
            motorcycle,
            mechanic_id,
            maintenance_needs,
            maintenance_gaps,
            ServiceOrderStatus.REQUESTED,
            events=(event,),
        )

    @property
    def current_proposal(self) -> ServiceProposal | None:
        return self.proposals[-1] if self.proposals else None

    def review(self, *, actor_id: str, accept: bool, reason: str | None = None) -> "ServiceOrder":
        self._require_mechanic(actor_id)
        self._require_status(ServiceOrderStatus.REQUESTED)
        if not accept and not (reason or "").strip():
            raise ValueError("rejection reason is required")
        status = ServiceOrderStatus.UNDER_REVIEW if accept else ServiceOrderStatus.REJECTED
        name = "service_request_reviewed" if accept else "service_request_rejected"
        return self._transition(status, ServiceOrderEvent(name, actor_id, (("reason", reason),)))

    def propose(
        self,
        *,
        actor_id: str,
        work_items: tuple[str, ...],
        parts: tuple[str, ...],
        price_cents: int,
        estimated_completion: date,
        notes: str | None = None,
    ) -> "ServiceOrder":
        self._require_mechanic(actor_id)
        if self.status not in {ServiceOrderStatus.UNDER_REVIEW, ServiceOrderStatus.NEGOTIATING}:
            raise ValueError(f"cannot propose service while order is {self.status.value}")
        proposal = ServiceProposal(
            len(self.proposals) + 1,
            work_items,
            parts,
            price_cents,
            estimated_completion,
            notes,
        )
        event = ServiceOrderEvent(
            "service_proposed",
            actor_id,
            (("proposal_version", proposal.version), ("price_cents", price_cents)),
        )
        return replace(
            self,
            status=ServiceOrderStatus.PROPOSED,
            proposals=self.proposals + (proposal,),
            events=self.events + (event,),
        )

    def respond_to_proposal(
        self, *, actor_id: str, accept: bool, reason: str | None = None
    ) -> "ServiceOrder":
        self._require_owner(actor_id)
        self._require_status(ServiceOrderStatus.PROPOSED)
        proposal = self.current_proposal
        if proposal is None:
            raise ValueError("service proposal is missing")
        if not accept and not (reason or "").strip():
            raise ValueError("proposal rejection reason is required")
        status = ServiceOrderStatus.AGREED if accept else ServiceOrderStatus.NEGOTIATING
        name = "service_proposal_accepted" if accept else "service_proposal_rejected"
        return replace(
            self,
            status=status,
            agreed_proposal_version=proposal.version if accept else None,
            events=self.events
            + (ServiceOrderEvent(name, actor_id, (("proposal_version", proposal.version), ("reason", reason))),),
        )

    def start(self, *, actor_id: str) -> "ServiceOrder":
        self._require_mechanic(actor_id)
        self._require_status(ServiceOrderStatus.AGREED)
        return self._transition(ServiceOrderStatus.IN_PROGRESS, ServiceOrderEvent("service_job_started", actor_id))

    def complete(self, *, actor_id: str, completion_notes: str) -> "ServiceOrder":
        self._require_mechanic(actor_id)
        self._require_status(ServiceOrderStatus.IN_PROGRESS)
        if not completion_notes.strip():
            raise ValueError("completion notes are required")
        return self._transition(
            ServiceOrderStatus.COMPLETED,
            ServiceOrderEvent("service_job_completed", actor_id, (("completion_notes", completion_notes),)),
        )

    def issue_invoice(self, *, actor_id: str) -> "ServiceOrder":
        self._require_mechanic(actor_id)
        self._require_status(ServiceOrderStatus.COMPLETED)
        proposal = self.current_proposal
        if proposal is None or proposal.version != self.agreed_proposal_version:
            raise ValueError("agreed proposal is required before invoicing")
        return replace(
            self,
            status=ServiceOrderStatus.AWAITING_PAYMENT,
            invoice_cents=proposal.price_cents,
            events=self.events
            + (ServiceOrderEvent("service_invoice_issued", actor_id, (("amount_cents", proposal.price_cents),)),),
        )

    def pay(self, *, actor_id: str, amount_cents: int, payment_reference: str) -> "ServiceOrder":
        self._require_owner(actor_id)
        self._require_status(ServiceOrderStatus.AWAITING_PAYMENT)
        if amount_cents != self.invoice_cents:
            raise ValueError("payment amount must match the invoice")
        if not payment_reference.strip():
            raise ValueError("payment reference is required")
        return replace(
            self,
            status=ServiceOrderStatus.PAID,
            payment_reference=payment_reference,
            events=self.events
            + (ServiceOrderEvent("service_payment_recorded", actor_id, (("amount_cents", amount_cents),)),),
        )

    def _transition(self, status: ServiceOrderStatus, event: ServiceOrderEvent) -> "ServiceOrder":
        return replace(self, status=status, events=self.events + (event,))

    def _require_owner(self, actor_id: str) -> None:
        if actor_id != self.motorcycle.owner_id:
            raise PermissionError("only the motorcycle owner may perform this action")

    def _require_mechanic(self, actor_id: str) -> None:
        if actor_id != self.mechanic_id:
            raise PermissionError("only the assigned mechanic may perform this action")

    def _require_status(self, expected: ServiceOrderStatus) -> None:
        if self.status != expected:
            raise ValueError(f"expected order status {expected.value}, got {self.status.value}")
