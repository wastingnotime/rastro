import unittest
from datetime import date

from app.application.use_cases import (
    CancelServiceOrder,
    CompleteServiceJob,
    CreateServiceRequest,
    IdentifyMotorcycle,
    IssueServiceInvoice,
    PayServiceJob,
    ProposeServiceWork,
    RespondToServiceProposal,
    ReviewServiceRequest,
    StartServiceJob,
)
from app.domain.maintenance import MaintenanceItem
from app.domain.service_order import ServiceOrderEvent, ServiceOrderStatus, ServiceProposal


class ServiceOrderWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.motorcycle = IdentifyMotorcycle().execute(
            motorcycle_id="moto-1",
            owner_id="owner-1",
            manufacturer="Honda",
            model="CB 500X",
            model_year=2024,
            registration="ABC1D23",
        )
        self.items = [
            MaintenanceItem(
                "Chain inspection",
                interval_km=3000,
                last_service_odometer_km=15900,
            )
        ]

    def request(self):
        return CreateServiceRequest().execute(
            order_id="order-1",
            motorcycle=self.motorcycle,
            actor_id="owner-1",
            mechanic_id="mechanic-1",
            maintenance_needs=("Chain inspection",),
            maintenance_gaps=("No recent chain condition photo",),
        )

    def agreed_order(self):
        order = ReviewServiceRequest().execute(
            self.request(), actor_id="mechanic-1", accept=True
        )
        order = ProposeServiceWork().execute(
            order,
            actor_id="mechanic-1",
            work_items=("Inspect and adjust chain",),
            parts=(),
            price_cents=22000,
            estimated_completion=date(2026, 8, 2),
        )
        return RespondToServiceProposal().execute(
            order, actor_id="owner-1", accept=True
        )

    def test_owner_and_mechanic_complete_negotiated_paid_service(self):
        order = ReviewServiceRequest().execute(
            self.request(), actor_id="mechanic-1", accept=True
        )
        order = ProposeServiceWork().execute(
            order,
            actor_id="mechanic-1",
            work_items=("Inspect and adjust chain",),
            parts=("Chain lubricant",),
            price_cents=25000,
            estimated_completion=date(2026, 8, 2),
        )
        order = RespondToServiceProposal().execute(
            order,
            actor_id="owner-1",
            accept=False,
            reason="Price is above budget",
        )
        self.assertEqual(order.status, ServiceOrderStatus.NEGOTIATING)
        order = ProposeServiceWork().execute(
            order,
            actor_id="mechanic-1",
            work_items=("Inspect and adjust chain",),
            parts=(),
            price_cents=22000,
            estimated_completion=date(2026, 8, 2),
        )
        order = RespondToServiceProposal().execute(
            order, actor_id="owner-1", accept=True
        )
        order = StartServiceJob().execute(order, actor_id="mechanic-1")
        order, updated_items, service_event = CompleteServiceJob().execute(
            order,
            self.items,
            actor_id="mechanic-1",
            completion_notes="Chain inspected, cleaned, and adjusted",
            serviced_at=date(2026, 8, 2),
            odometer_km=18510,
        )
        order = IssueServiceInvoice().execute(order, actor_id="mechanic-1")
        order = PayServiceJob().execute(
            order,
            actor_id="owner-1",
            amount_cents=22000,
            payment_reference="payment-1",
        )

        self.assertEqual(order.status, ServiceOrderStatus.PAID)
        self.assertEqual([proposal.version for proposal in order.proposals], [1, 2])
        self.assertEqual(order.agreed_proposal_version, 2)
        self.assertEqual(order.invoice_cents, 22000)
        self.assertEqual(updated_items[0].last_service_odometer_km, 18510)
        self.assertEqual(service_event.service_id, "order-1")
        self.assertEqual(dict(order.events[-4].details), {"proposal_version": 2, "price_cents": 22000})
        self.assertEqual(dict(order.events[-3].details)["order_id"], "order-1")
        self.assertEqual(
            dict(order.events[-2].details),
            {"amount_cents": 22000, "proposal_version": 2},
        )
        self.assertEqual(
            dict(order.events[-1].details),
            {"amount_cents": 22000, "proposal_version": 2, "payment_reference": "payment-1"},
        )
        self.assertEqual(
            [event.name for event in order.events],
            [
                "service_requested",
                "service_request_reviewed",
                "service_proposed",
                "service_proposal_rejected",
                "service_proposed",
                "service_proposal_accepted",
                "service_job_started",
                "service_job_completed",
                "service_invoice_issued",
                "service_payment_recorded",
            ],
        )
        self.assertEqual(order.event_names, tuple(event.name for event in order.events))

    def test_mechanic_can_reject_request_with_reason(self):
        order = ReviewServiceRequest().execute(
            self.request(),
            actor_id="mechanic-1",
            accept=False,
            reason="Required equipment is unavailable",
        )
        self.assertEqual(order.status, ServiceOrderStatus.REJECTED)

    def test_owner_can_cancel_before_work_starts(self):
        cancelled = CancelServiceOrder().execute(
            self.request(), actor_id="owner-1", reason="Found another mechanic"
        )
        self.assertEqual(cancelled.status, ServiceOrderStatus.CANCELLED)
        self.assertEqual(cancelled.events[-1].name, "service_order_cancelled")

    def test_cancel_requires_reason_and_cannot_cancel_started_work(self):
        with self.assertRaises(ValueError):
            CancelServiceOrder().execute(self.request(), actor_id="owner-1", reason=" ")
        started = StartServiceJob().execute(self.agreed_order(), actor_id="mechanic-1")
        with self.assertRaises(ValueError):
            CancelServiceOrder().execute(started, actor_id="owner-1", reason="No longer needed")

    def test_request_rejects_blank_maintenance_gap(self):
        with self.assertRaises(ValueError):
            CreateServiceRequest().execute(
                order_id="order-1",
                motorcycle=self.motorcycle,
                actor_id="owner-1",
                mechanic_id="mechanic-1",
                maintenance_needs=("Chain inspection",),
                maintenance_gaps=("  ",),
            )

    def test_request_rejects_duplicate_maintenance_need(self):
        with self.assertRaisesRegex(ValueError, "cannot be duplicated"):
            CreateServiceRequest().execute(
                order_id="order-1",
                motorcycle=self.motorcycle,
                actor_id="owner-1",
                mechanic_id="mechanic-1",
                maintenance_needs=("Chain inspection", "Chain inspection"),
            )

    def test_order_rejects_blank_identity_when_constructed_directly(self):
        with self.assertRaisesRegex(ValueError, "order id is required"):
            self.request().__class__(
                " ", self.motorcycle, "mechanic-1", ("Chain inspection",), (), ServiceOrderStatus.REQUESTED
            )

    def test_motorcycle_rejects_blank_optional_registration(self):
        with self.assertRaisesRegex(ValueError, "registration must not be blank"):
            IdentifyMotorcycle().execute(
                motorcycle_id="moto-1",
                owner_id="owner-1",
                manufacturer="Honda",
                model="CB 500X",
                model_year=2024,
                registration="  ",
            )

    def test_motorcycle_rejects_invalid_scalar_types(self):
        with self.assertRaises(ValueError):
            IdentifyMotorcycle().execute(
                motorcycle_id=1, owner_id="owner-1", manufacturer="Honda", model="CB 500X", model_year=2024
            )
        with self.assertRaises(ValueError):
            IdentifyMotorcycle().execute(
                motorcycle_id="moto-1", owner_id="owner-1", manufacturer="Honda", model="CB 500X", model_year=True
            )

    def test_event_requires_name_and_actor(self):
        with self.assertRaises(ValueError):
            ServiceOrderEvent("", "owner-1")
        with self.assertRaises(ValueError):
            ServiceOrderEvent("service_requested", " ")
        with self.assertRaises(ValueError):
            ServiceOrderEvent(1, "owner-1")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            ServiceOrderEvent("service_requested", 1)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            ServiceOrderEvent("service_requested", "owner-1", ((" ", "value"),))
        with self.assertRaises(ValueError):
            ServiceOrderEvent("service_requested", "owner-1", ((1, "value"),))  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "detail keys cannot be duplicated"):
            ServiceOrderEvent("service_requested", "owner-1", (("id", 1), ("id", 2)))

    def test_proposal_rejects_blank_part(self):
        with self.assertRaises(ValueError):
            ProposeServiceWork().execute(
                self.agreed_order(),
                actor_id="mechanic-1",
                work_items=("Inspect and adjust chain",),
                parts=("  ",),
                price_cents=22000,
                estimated_completion=date(2026, 8, 2),
            )

    def test_proposal_rejects_duplicate_work_item(self):
        with self.assertRaisesRegex(ValueError, "work items cannot be duplicated"):
            ProposeServiceWork().execute(
                self.request_reviewed(),
                actor_id="mechanic-1",
                work_items=("Inspect chain", "Inspect chain"),
                parts=(),
                price_cents=22000,
                estimated_completion=date(2026, 8, 2),
            )

    def test_proposal_rejects_invalid_scalar_types(self):
        with self.assertRaises(ValueError):
            ServiceProposal(True, ("Inspect chain",), (), 22000, date(2026, 8, 2))  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            ServiceProposal(1, ("Inspect chain",), (), True, date(2026, 8, 2))  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            ServiceProposal(1, ("Inspect chain",), (), 22000, "tomorrow")  # type: ignore[arg-type]

    def request_reviewed(self):
        return ReviewServiceRequest().execute(
            self.request(), actor_id="mechanic-1", accept=True
        )

    def test_unassigned_mechanic_cannot_review_or_start_work(self):
        with self.assertRaises(PermissionError):
            ReviewServiceRequest().execute(
                self.request(), actor_id="mechanic-2", accept=True
            )
        with self.assertRaises(PermissionError):
            StartServiceJob().execute(self.agreed_order(), actor_id="mechanic-2")

    def test_work_cannot_start_before_owner_accepts_proposal(self):
        order = ReviewServiceRequest().execute(
            self.request(), actor_id="mechanic-1", accept=True
        )
        with self.assertRaises(ValueError):
            StartServiceJob().execute(order, actor_id="mechanic-1")

    def test_payment_must_match_agreed_invoice(self):
        order = StartServiceJob().execute(self.agreed_order(), actor_id="mechanic-1")
        order, _, _ = CompleteServiceJob().execute(
            order,
            self.items,
            actor_id="mechanic-1",
            completion_notes="Chain adjusted",
            serviced_at=date(2026, 8, 2),
            odometer_km=18510,
        )
        order = IssueServiceInvoice().execute(order, actor_id="mechanic-1")
        with self.assertRaises(ValueError):
            PayServiceJob().execute(
                order,
                actor_id="owner-1",
                amount_cents=21000,
                payment_reference="payment-1",
            )

    def test_payment_rejects_non_positive_amount(self):
        order = StartServiceJob().execute(self.agreed_order(), actor_id="mechanic-1")
        order, _, _ = CompleteServiceJob().execute(
            order,
            self.items,
            actor_id="mechanic-1",
            completion_notes="Chain adjusted",
            serviced_at=date(2026, 8, 2),
            odometer_km=18510,
        )
        order = IssueServiceInvoice().execute(order, actor_id="mechanic-1")
        with self.assertRaisesRegex(ValueError, "payment amount must be positive"):
            PayServiceJob().execute(
                order,
                actor_id="owner-1",
                amount_cents=0,
                payment_reference="payment-1",
            )

    def test_completion_rejects_history_gap_before_transition(self):
        order = StartServiceJob().execute(self.agreed_order(), actor_id="mechanic-1")
        with self.assertRaises(ValueError):
            CompleteServiceJob().execute(
                order,
                [],
                actor_id="mechanic-1",
                completion_notes="Chain adjusted",
                serviced_at=date(2026, 8, 2),
                odometer_km=18510,
            )
        self.assertEqual(order.status, ServiceOrderStatus.IN_PROGRESS)

    def test_owner_cannot_respond_to_stale_proposal_version(self):
        order = ReviewServiceRequest().execute(
            self.request(), actor_id="mechanic-1", accept=True
        )
        order = ProposeServiceWork().execute(
            order,
            actor_id="mechanic-1",
            work_items=("Inspect and adjust chain",),
            parts=(),
            price_cents=22000,
            estimated_completion=date(2026, 8, 2),
        )
        with self.assertRaisesRegex(ValueError, "proposal response is stale"):
            RespondToServiceProposal().execute(
                order,
                actor_id="owner-1",
                accept=True,
                proposal_version=2,
            )
        self.assertEqual(order.status, ServiceOrderStatus.PROPOSED)


if __name__ == "__main__":
    unittest.main()
