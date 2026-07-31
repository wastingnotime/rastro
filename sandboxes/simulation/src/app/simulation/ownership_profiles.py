from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

from app.domain.maintenance import MaintenanceItem, MaintenanceStatus, MotorcycleState, assess


@dataclass(frozen=True)
class OwnershipProfile:
    name: str
    kilometers_on: Callable[[date], int]
    records_odometer_on: Callable[[date], bool]


@dataclass(frozen=True)
class ProfileResult:
    profile: str
    days: int
    status_counts: dict[str, int]
    unknown_days: int
    attention_days: int


def simulate_profile(
    profile: OwnershipProfile,
    *,
    start_date: date,
    days: int,
    starting_odometer_km: int,
    item: MaintenanceItem,
    odometer_stale_after_days: int = 90,
) -> ProfileResult:
    current_odometer = starting_odometer_km
    last_recorded_at = start_date
    counts: Counter[str] = Counter()
    for offset in range(days):
        current_date = start_date + timedelta(days=offset)
        current_odometer += profile.kilometers_on(current_date)
        if profile.records_odometer_on(current_date):
            last_recorded_at = current_date
        result = assess(
            item,
            MotorcycleState(current_date, current_odometer, last_recorded_at),
            odometer_stale_after_days=odometer_stale_after_days,
        )
        counts[result.status.value] += 1
    return ProfileResult(
        profile=profile.name,
        days=days,
        status_counts=dict(counts),
        unknown_days=counts[MaintenanceStatus.UNKNOWN.value],
        attention_days=sum(
            counts[status.value]
            for status in (
                MaintenanceStatus.APPROACHING_DUE,
                MaintenanceStatus.DUE,
                MaintenanceStatus.OVERDUE,
            )
        ),
    )


def daily_commuter() -> OwnershipProfile:
    return OwnershipProfile("daily_commuter", lambda current_date: 30, lambda current_date: True)


def weekend_rider() -> OwnershipProfile:
    return OwnershipProfile(
        "weekend_rider",
        lambda current_date: 80 if current_date.weekday() >= 5 else 0,
        lambda current_date: current_date.weekday() >= 5,
    )


def long_unused() -> OwnershipProfile:
    return OwnershipProfile("long_unused", lambda current_date: 0, lambda current_date: False)
