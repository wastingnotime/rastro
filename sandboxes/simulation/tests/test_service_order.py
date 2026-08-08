import unittest
from datetime import date

from app.application.use_cases import (
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
from app.domain.service_order import ServiceOrderStatus


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

    def test_mechanic_can_reject_request_with_reason(self):
        order = ReviewServiceRequest().execute(
            self.request(),
            actor_id="mechanic-1",
            accept=False,
            reason="Required equipment is unavailable",
        )
        self.assertEqual(order.status, ServiceOrderStatus.REJECTED)

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


if __name__ == "__main__":
    unittest.main()
