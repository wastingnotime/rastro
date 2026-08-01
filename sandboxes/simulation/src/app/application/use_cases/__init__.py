"""Explicit application use cases for the motorcycle maintenance simulation."""

from dataclasses import dataclass
from enum import Enum

from app.application.use_cases.correct_service_record import CorrectServiceRecord
from app.application.use_cases.record_odometer_reading import RecordOdometerReading
from app.application.use_cases.record_service import RecordService
from app.application.use_cases.sync_attention_preferences import SyncAttentionPreferences
from app.application.use_cases.view_owner_status import ViewOwnerStatus


class UseCaseKind(str, Enum):
    COMMAND = "command"
    QUERY = "query"


@dataclass(frozen=True)
class UseCaseDefinition:
    name: str
    kind: UseCaseKind
    purpose: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("use-case name is required")
        if not self.purpose.strip():
            raise ValueError("use-case purpose is required")


USE_CASE_CATALOG = (
    UseCaseDefinition(
        "ViewOwnerStatus",
        UseCaseKind.QUERY,
        "View maintenance and document attention for one motorcycle.",
    ),
    UseCaseDefinition(
        "RecordService",
        UseCaseKind.COMMAND,
        "Record a service visit against selected maintenance items.",
    ),
    UseCaseDefinition(
        "CorrectServiceRecord",
        UseCaseKind.COMMAND,
        "Correct an incorrect service record without deleting history.",
    ),
    UseCaseDefinition(
        "SyncAttentionPreferences",
        UseCaseKind.COMMAND,
        "Synchronize owner attention-view preferences across devices.",
    ),
    UseCaseDefinition(
        "RecordOdometerReading",
        UseCaseKind.COMMAND,
        "Append a normal or explicitly linked corrective odometer reading.",
    ),
)

USE_CASE_KINDS = {definition.name: definition.kind for definition in USE_CASE_CATALOG}

__all__ = [
    "CorrectServiceRecord",
    "RecordOdometerReading",
    "RecordService",
    "SyncAttentionPreferences",
    "ViewOwnerStatus",
    "USE_CASE_KINDS",
    "USE_CASE_CATALOG",
    "UseCaseKind",
    "UseCaseDefinition",
]
