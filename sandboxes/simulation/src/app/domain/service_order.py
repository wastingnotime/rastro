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
            if not isinstance(value, str) or not value.strip():
                raise ValueError(message)
        if not isinstance(self.model_year, int) or isinstance(self.model_year, bool) or self.model_year < 1885:
            raise ValueError("motorcycle model year is invalid")
        if self.registration is not None and (
            not isinstance(self.registration, str) or not self.registration.strip()
        ):
            raise ValueError("motorcycle registration must not be blank")


@dataclass(frozen=True)
class ServiceProposal:
    version: int
    work_items: tuple[str, ...]
    parts: tuple[str, ...]
    price_cents: int
    estimated_completion: date
    notes: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version < 1:
            raise ValueError("proposal version must be positive")
        if not self.work_items or any(not item.strip() for item in self.work_items):
            raise ValueError("proposal work items are required")
        if len(set(self.work_items)) != len(self.work_items):
            raise ValueError("proposal work items cannot be duplicated")
        if any(not part.strip() for part in self.parts):
            raise ValueError("proposal parts must not be blank")
        if not isinstance(self.price_cents, int) or isinstance(self.price_cents, bool) or self.price_cents <= 0:
            raise ValueError("proposal price must be positive")
        if not isinstance(self.estimated_completion, date):
            raise ValueError("proposal completion date is invalid")
        if self.notes is not None and (
            not isinstance(self.notes, str) or not self.notes.strip()
        ):
            raise ValueError("proposal notes must not be blank")


@dataclass(frozen=True)
class ServiceOrderEvent:
    name: str
    actor_id: str
    details: tuple[tuple[str, object], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("service order event name is required")
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise ValueError("service order event actor is required")
        keys = [key for key, _ in self.details]
        if any(not isinstance(key, str) or not key.strip() for key in keys):
            raise ValueError("service order event detail keys are required")
        if len(set(keys)) != len(keys):
            raise ValueError("service order event detail keys cannot be duplicated")


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

    def __post_init__(self) -> None:
        if not self.order_id.strip():
            raise ValueError("order id is required")
        if not self.mechanic_id.strip():
            raise ValueError("mechanic id is required")
        if not isinstance(self.status, ServiceOrderStatus):
            raise ValueError("service order status is invalid")
        if not self.maintenance_needs or any(not item.strip() for item in self.maintenance_needs):
            raise ValueError("at least one maintenance need is required")
        if len(set(self.maintenance_needs)) != len(self.maintenance_needs):
            raise ValueError("maintenance needs cannot be duplicated")
        if any(not item.strip() for item in self.maintenance_gaps):
            raise ValueError("maintenance gaps must not be blank")
        if len(set(self.maintenance_gaps)) != len(self.maintenance_gaps):
            raise ValueError("maintenance gaps cannot be duplicated")

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
        if any(not item.strip() for item in maintenance_gaps):
            raise ValueError("maintenance gaps must not be blank")
        if len(set(maintenance_needs)) != len(maintenance_needs):
            raise ValueError("maintenance needs cannot be duplicated")
        if len(set(maintenance_gaps)) != len(maintenance_gaps):
            raise ValueError("maintenance gaps cannot be duplicated")
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

    @property
    def event_names(self) -> tuple[str, ...]:
        """Return the ordered event contract without exposing event storage."""
        return tuple(event.name for event in self.events)

    @property
    def latest_event(self) -> ServiceOrderEvent | None:
        return self.events[-1] if self.events else None

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
        self,
        *,
        actor_id: str,
        accept: bool,
        reason: str | None = None,
        proposal_version: int | None = None,
    ) -> "ServiceOrder":
        self._require_owner(actor_id)
        self._require_status(ServiceOrderStatus.PROPOSED)
        proposal = self.current_proposal
        if proposal is None:
            raise ValueError("service proposal is missing")
        if proposal_version is not None and proposal_version != proposal.version:
            raise ValueError("proposal response is stale")
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
        proposal = self.current_proposal
        if proposal is None or proposal.version != self.agreed_proposal_version:
            raise ValueError("agreed proposal is required before starting work")
        return self._transition(
            ServiceOrderStatus.IN_PROGRESS,
            ServiceOrderEvent(
                "service_job_started",
                actor_id,
                (("proposal_version", proposal.version), ("price_cents", proposal.price_cents)),
            ),
        )

    def cancel(self, *, actor_id: str, reason: str) -> "ServiceOrder":
        if actor_id not in {self.motorcycle.owner_id, self.mechanic_id}:
            raise PermissionError("only the owner or assigned mechanic may cancel")
        if self.status not in {
            ServiceOrderStatus.REQUESTED,
            ServiceOrderStatus.UNDER_REVIEW,
            ServiceOrderStatus.PROPOSED,
            ServiceOrderStatus.NEGOTIATING,
            ServiceOrderStatus.AGREED,
        }:
            raise ValueError(f"cannot cancel service while order is {self.status.value}")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("cancellation reason is required")
        return self._transition(
            ServiceOrderStatus.CANCELLED,
            ServiceOrderEvent("service_order_cancelled", actor_id, (("reason", reason),)),
        )

    def complete(self, *, actor_id: str, completion_notes: str) -> "ServiceOrder":
        self._require_mechanic(actor_id)
        self._require_status(ServiceOrderStatus.IN_PROGRESS)
        if not completion_notes.strip():
            raise ValueError("completion notes are required")
        return self._transition(
            ServiceOrderStatus.COMPLETED,
            ServiceOrderEvent(
                "service_job_completed",
                actor_id,
                (("order_id", self.order_id), ("completion_notes", completion_notes)),
            ),
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
            + (ServiceOrderEvent(
                "service_invoice_issued",
                actor_id,
                (("amount_cents", proposal.price_cents), ("proposal_version", proposal.version)),
            ),),
        )

    def pay(self, *, actor_id: str, amount_cents: int, payment_reference: str) -> "ServiceOrder":
        self._require_owner(actor_id)
        self._require_status(ServiceOrderStatus.AWAITING_PAYMENT)
        if amount_cents <= 0:
            raise ValueError("payment amount must be positive")
        if amount_cents != self.invoice_cents:
            raise ValueError("payment amount must match the invoice")
        if not payment_reference.strip():
            raise ValueError("payment reference is required")
        return replace(
            self,
            status=ServiceOrderStatus.PAID,
            payment_reference=payment_reference,
            events=self.events
            + (ServiceOrderEvent(
                "service_payment_recorded",
                actor_id,
                (("amount_cents", amount_cents), ("proposal_version", self.agreed_proposal_version), ("payment_reference", payment_reference)),
            ),),
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
