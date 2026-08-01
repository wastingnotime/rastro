from __future__ import annotations

from typing import Protocol

from app.application.attention_sync import AttentionPreferenceSnapshot


class AttentionPreferenceStore(Protocol):
    def load(self, owner_id: str, scope_id: str) -> AttentionPreferenceSnapshot | None:
        """Load the latest snapshot for one owner and motorcycle."""

    def save(self, snapshot: AttentionPreferenceSnapshot) -> AttentionPreferenceSnapshot:
        """Merge and return the stored winner."""
