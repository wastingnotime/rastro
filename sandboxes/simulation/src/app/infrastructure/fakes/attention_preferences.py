from __future__ import annotations

from app.application.attention_sync import AttentionPreferenceSnapshot, merge_preference_snapshots


class InMemoryAttentionPreferenceStore:
    """Deterministic fake for account-owned preference storage."""

    def __init__(self) -> None:
        self._snapshots: dict[tuple[str, str], AttentionPreferenceSnapshot] = {}

    def load(self, owner_id: str, scope_id: str) -> AttentionPreferenceSnapshot | None:
        return self._snapshots.get((owner_id, scope_id))

    def save(self, snapshot: AttentionPreferenceSnapshot) -> AttentionPreferenceSnapshot:
        key = (snapshot.owner_id, snapshot.scope_id)
        current = self._snapshots.get(key)
        winner = merge_preference_snapshots(current, snapshot) if current else snapshot
        self._snapshots[key] = winner
        return winner
