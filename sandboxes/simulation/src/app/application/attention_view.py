from __future__ import annotations

from dataclasses import dataclass

from app.domain.maintenance import AttentionGroup


@dataclass(frozen=True)
class AttentionGroupView:
    status: str
    item_titles: tuple[str, ...]
    expanded: bool


def build_attention_view(
    groups: list[AttentionGroup], *, expand_all: bool = False
) -> list[AttentionGroupView]:
    """Keep the primary group open and lower-priority context collapsed by default."""
    return [
        AttentionGroupView(
            status=group.status.value,
            item_titles=tuple(item.title for item in group.items),
            expanded=expand_all or index == 0,
        )
        for index, group in enumerate(groups)
    ]
