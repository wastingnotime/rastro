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


@dataclass(frozen=True)
class AttentionSyncState:
    owner_id: str
    snapshots: tuple[AttentionPreferenceSnapshot, ...] = ()


@dataclass(frozen=True)
class AttentionSyncResponse:
    accepted: bool
    code: str
    message: str
    snapshot: AttentionPreferenceSnapshot | None = None


def snapshot_preferences(
    preferences: AttentionViewPreferences,
    *,
    owner_id: str,
    revision: int,
    device_id: str,
) -> AttentionPreferenceSnapshot:
    if not owner_id.strip():
        raise ValueError("owner id is required")
    if not preferences.scope_id.strip():
        raise ValueError("motorcycle scope id is required")
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


def handle_preference_sync(
    state: AttentionSyncState,
    actor_id: str,
    incoming: AttentionPreferenceSnapshot,
) -> tuple[AttentionSyncState, AttentionSyncResponse]:
    """Authorize and merge one device snapshot into owner-scoped state."""
    if actor_id != state.owner_id or incoming.owner_id != state.owner_id:
        return state, AttentionSyncResponse(
            False,
            "preference_sync_forbidden",
            "Only the preference owner can synchronize attention settings.",
        )
    existing = next(
        (snapshot for snapshot in state.snapshots if snapshot.scope_id == incoming.scope_id),
        None,
    )
    winner = merge_preference_snapshots(existing, incoming) if existing else incoming
    snapshots = tuple(
        snapshot
        for snapshot in state.snapshots
        if snapshot.scope_id != incoming.scope_id
    ) + (winner,)
    updated = AttentionSyncState(state.owner_id, snapshots)
    return updated, AttentionSyncResponse(
        True,
        "preference_sync_accepted",
        "Attention preferences synchronized.",
        snapshot=winner,
    )
