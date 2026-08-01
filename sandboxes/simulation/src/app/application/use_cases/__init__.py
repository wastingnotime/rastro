"""Explicit application use cases for the motorcycle maintenance simulation."""

from enum import Enum

from app.application.use_cases.correct_service_record import CorrectServiceRecord
from app.application.use_cases.record_odometer_reading import RecordOdometerReading
from app.application.use_cases.record_service import RecordService
from app.application.use_cases.sync_attention_preferences import SyncAttentionPreferences
from app.application.use_cases.view_owner_status import ViewOwnerStatus


class UseCaseKind(str, Enum):
    COMMAND = "command"
    QUERY = "query"


USE_CASE_KINDS = {
    "ViewOwnerStatus": UseCaseKind.QUERY,
    "RecordService": UseCaseKind.COMMAND,
    "CorrectServiceRecord": UseCaseKind.COMMAND,
    "SyncAttentionPreferences": UseCaseKind.COMMAND,
    "RecordOdometerReading": UseCaseKind.COMMAND,
}

__all__ = [
    "CorrectServiceRecord",
    "RecordOdometerReading",
    "RecordService",
    "SyncAttentionPreferences",
    "ViewOwnerStatus",
    "USE_CASE_KINDS",
    "UseCaseKind",
]
