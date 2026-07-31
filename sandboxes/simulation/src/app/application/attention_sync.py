from __future__ import annotations

from dataclasses import dataclass

from app.application.attention_view import AttentionViewPreferences


@dataclass(frozen=True)
class AttentionPreferenceSnapshot:
    owner_id: str
    scope_id: str
    expanded_statuses: frozenset[str]
    revision: int
    device_id: str


def snapshot_preferences(
    preferences: AttentionViewPreferences,
    *,
    owner_id: str,
    revision: int,
    device_id: str,
) -> AttentionPreferenceSnapshot:
    if not owner_id.strip():
        raise ValueError("owner id is required")
    if revision < 0:
        raise ValueError("preference revision cannot be negative")
    if not device_id.strip():
        raise ValueError("device id is required")
    return AttentionPreferenceSnapshot(
        owner_id,
        preferences.scope_id,
        preferences.expanded_statuses,
        revision,
        device_id,
    )


def merge_preference_snapshots(
    local: AttentionPreferenceSnapshot,
    remote: AttentionPreferenceSnapshot,
) -> AttentionPreferenceSnapshot:
    """Choose a deterministic winner for same-motorcycle cross-device sync."""
    if local.owner_id != remote.owner_id:
        raise ValueError("preference snapshots must share an owner")
    if local.scope_id != remote.scope_id:
        raise ValueError("preference snapshots must share a motorcycle scope")
    return max(
        (local, remote),
        key=lambda snapshot: (snapshot.revision, snapshot.device_id),
    )


def preferences_from_snapshot(
    snapshot: AttentionPreferenceSnapshot,
) -> AttentionViewPreferences:
    return AttentionViewPreferences(snapshot.scope_id, snapshot.expanded_statuses)
