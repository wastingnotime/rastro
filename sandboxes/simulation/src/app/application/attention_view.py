from __future__ import annotations

from dataclasses import dataclass

from app.domain.maintenance import AttentionGroup


@dataclass(frozen=True)
class AttentionGroupView:
    status: str
    item_titles: tuple[str, ...]
    expanded: bool


@dataclass(frozen=True)
class AttentionViewPreferences:
    scope_id: str
    expanded_statuses: frozenset[str] = frozenset()


def build_attention_view(
    groups: list[AttentionGroup],
    *,
    expand_all: bool = False,
    preferences: AttentionViewPreferences | None = None,
    scope_id: str | None = None,
) -> list[AttentionGroupView]:
    """Apply persisted expansion choices without changing attention priority."""
    expanded_statuses = (
        preferences.expanded_statuses
        if preferences is not None and (scope_id is None or preferences.scope_id == scope_id)
        else frozenset()
    )
    return [
        AttentionGroupView(
            status=group.status.value,
            item_titles=tuple(item.title for item in group.items),
            expanded=expand_all or index == 0 or group.status.value in expanded_statuses,
        )
        for index, group in enumerate(groups)
    ]


def toggle_group(
    preferences: AttentionViewPreferences, status: str
) -> AttentionViewPreferences:
    expanded = set(preferences.expanded_statuses)
    if status in expanded:
        expanded.remove(status)
    else:
        expanded.add(status)
    return AttentionViewPreferences(preferences.scope_id, frozenset(expanded))
