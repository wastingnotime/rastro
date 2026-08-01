from __future__ import annotations

from app.application.attention_sync import (
    AttentionPreferenceSnapshot,
    AttentionSyncResponse,
    AttentionSyncState,
    handle_preference_sync,
)


class SyncAttentionPreferences:
    """Owner command for synchronizing one device's attention-view settings."""

    def execute(
        self,
        state: AttentionSyncState,
        *,
        actor_id: str,
        incoming: AttentionPreferenceSnapshot,
    ) -> tuple[AttentionSyncState, AttentionSyncResponse]:
        return handle_preference_sync(state, actor_id, incoming)
