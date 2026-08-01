"""Explicit application use cases for the motorcycle maintenance simulation."""

from dataclasses import dataclass
from enum import Enum

from app.application.use_cases.correct_service_record import CorrectServiceRecord
from app.application.use_cases.customize_warning_thresholds import CustomizeWarningThresholds
from app.application.use_cases.record_odometer_reading import RecordOdometerReading
from app.application.use_cases.record_service import RecordService
from app.application.use_cases.sync_attention_preferences import SyncAttentionPreferences
from app.application.use_cases.view_owner_status import ViewOwnerStatus
from app.application.use_cases.view_service_history import ViewServiceHistory


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
    "CustomizeWarningThresholds",
    "RecordOdometerReading",
    "RecordService",
    "SyncAttentionPreferences",
    "ViewOwnerStatus",
    "ViewServiceHistory",
    "USE_CASE_KINDS",
    "USE_CASE_IDS",
    "USE_CASE_CATALOG",
    "UseCaseKind",
    "UseCaseDefinition",
    "index_use_case_catalog",
]
