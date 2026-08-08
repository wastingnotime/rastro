"""Explicit application use cases for the motorcycle maintenance simulation."""

from dataclasses import dataclass
from enum import Enum

from app.application.use_cases.correct_service_record import CorrectServiceRecord
from app.application.use_cases.customize_warning_thresholds import CustomizeWarningThresholds
from app.application.use_cases.record_odometer_reading import RecordOdometerReading
from app.application.use_cases.record_service import RecordService
from app.application.use_cases.restore_manufacturer_warning_thresholds import (
    RestoreManufacturerWarningThresholds,
)
from app.application.use_cases.service_order_workflow import (
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
from app.application.use_cases.sync_attention_preferences import SyncAttentionPreferences
from app.application.use_cases.view_owner_status import ViewOwnerStatus
from app.application.use_cases.view_service_history import ViewServiceHistory
from app.application.use_cases.view_warning_threshold_history import (
    ViewWarningThresholdHistory,
    WarningThresholdHistoryViewForbidden,
)


class UseCaseKind(str, Enum):
    COMMAND = "command"
    QUERY = "query"


@dataclass(frozen=True)
class UseCaseDefinition:
    use_case_id: str
    name: str
    kind: UseCaseKind
    purpose: str

    def __post_init__(self) -> None:
        if not self.use_case_id.strip():
            raise ValueError("use-case id is required")
        if not self.name.strip():
            raise ValueError("use-case name is required")
        if not self.purpose.strip():
            raise ValueError("use-case purpose is required")


USE_CASE_CATALOG = (
    UseCaseDefinition(
        "view-owner-status",
        "ViewOwnerStatus",
        UseCaseKind.QUERY,
        "View maintenance and document attention for one motorcycle.",
    ),
    UseCaseDefinition(
        "view-service-history",
        "ViewServiceHistory",
        UseCaseKind.QUERY,
        "View owner-authorized active service records for one motorcycle.",
    ),
    UseCaseDefinition(
        "view-warning-threshold-history",
        "ViewWarningThresholdHistory",
        UseCaseKind.QUERY,
        "View effective warning policy and its append-only threshold events.",
    ),
    UseCaseDefinition(
        "record-service",
        "RecordService",
        UseCaseKind.COMMAND,
        "Record a service visit against selected maintenance items.",
    ),
    UseCaseDefinition(
        "customize-warning-thresholds",
        "CustomizeWarningThresholds",
        UseCaseKind.COMMAND,
        "Customize maintenance warning thresholds while retaining an audit event.",
    ),
    UseCaseDefinition(
        "restore-manufacturer-warning-thresholds",
        "RestoreManufacturerWarningThresholds",
        UseCaseKind.COMMAND,
        "Restore canonical warning thresholds while retaining an audit event.",
    ),
    UseCaseDefinition(
        "correct-service-record",
        "CorrectServiceRecord",
        UseCaseKind.COMMAND,
        "Correct an incorrect service record without deleting history.",
    ),
    UseCaseDefinition(
        "sync-attention-preferences",
        "SyncAttentionPreferences",
        UseCaseKind.COMMAND,
        "Synchronize owner attention-view preferences across devices.",
    ),
    UseCaseDefinition(
        "record-odometer-reading",
        "RecordOdometerReading",
        UseCaseKind.COMMAND,
        "Append a normal or explicitly linked corrective odometer reading.",
    ),
    UseCaseDefinition(
        "identify-motorcycle",
        "IdentifyMotorcycle",
        UseCaseKind.COMMAND,
        "Identify an owner-bound motorcycle before assessing its maintenance needs.",
    ),
    UseCaseDefinition(
        "create-service-request",
        "CreateServiceRequest",
        UseCaseKind.COMMAND,
        "Send maintenance needs and known information gaps to a mechanic.",
    ),
    UseCaseDefinition(
        "review-service-request",
        "ReviewServiceRequest",
        UseCaseKind.COMMAND,
        "Let the assigned mechanic accept or reject a service request for review.",
    ),
    UseCaseDefinition(
        "propose-service-work",
        "ProposeServiceWork",
        UseCaseKind.COMMAND,
        "Propose work, parts, price, and timing for an owner request.",
    ),
    UseCaseDefinition(
        "respond-to-service-proposal",
        "RespondToServiceProposal",
        UseCaseKind.COMMAND,
        "Let the owner accept or reject a proposal while preserving negotiation history.",
    ),
    UseCaseDefinition(
        "start-service-job",
        "StartServiceJob",
        UseCaseKind.COMMAND,
        "Start mechanic work only after owner and mechanic agree.",
    ),
    UseCaseDefinition(
        "complete-service-job",
        "CompleteServiceJob",
        UseCaseKind.COMMAND,
        "Complete agreed work and update the motorcycle maintenance history.",
    ),
    UseCaseDefinition(
        "issue-service-invoice",
        "IssueServiceInvoice",
        UseCaseKind.COMMAND,
        "Invoice the exact price accepted in the service proposal.",
    ),
    UseCaseDefinition(
        "pay-service-job",
        "PayServiceJob",
        UseCaseKind.COMMAND,
        "Record owner payment for completed and invoiced work.",
    ),
)

def index_use_case_catalog(
    catalog: tuple[UseCaseDefinition, ...],
) -> tuple[dict[str, UseCaseKind], dict[str, str]]:
    names: set[str] = set()
    ids: set[str] = set()
    kinds: dict[str, UseCaseKind] = {}
    use_case_ids: dict[str, str] = {}
    for definition in catalog:
        if definition.name in names:
            raise ValueError(f"duplicate use-case name: {definition.name}")
        if definition.use_case_id in ids:
            raise ValueError(f"duplicate use-case id: {definition.use_case_id}")
        names.add(definition.name)
        ids.add(definition.use_case_id)
        kinds[definition.name] = definition.kind
        use_case_ids[definition.name] = definition.use_case_id
    return kinds, use_case_ids


USE_CASE_KINDS, USE_CASE_IDS = index_use_case_catalog(USE_CASE_CATALOG)

__all__ = [
    "CorrectServiceRecord",
    "CompleteServiceJob",
    "CreateServiceRequest",
    "CustomizeWarningThresholds",
    "IdentifyMotorcycle",
    "IssueServiceInvoice",
    "PayServiceJob",
    "ProposeServiceWork",
    "RecordOdometerReading",
    "RecordService",
    "RestoreManufacturerWarningThresholds",
    "RespondToServiceProposal",
    "ReviewServiceRequest",
    "StartServiceJob",
    "SyncAttentionPreferences",
    "ViewOwnerStatus",
    "ViewServiceHistory",
    "ViewWarningThresholdHistory",
    "WarningThresholdHistoryViewForbidden",
    "USE_CASE_KINDS",
    "USE_CASE_IDS",
    "USE_CASE_CATALOG",
    "UseCaseKind",
    "UseCaseDefinition",
    "index_use_case_catalog",
]
