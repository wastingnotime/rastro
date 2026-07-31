from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class MaintenanceStatus(str, Enum):
    OK = "ok"
    APPROACHING_DUE = "approaching_due"
    DUE = "due"
    OVERDUE = "overdue"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MotorcycleState:
    current_date: date
    odometer_km: int | None
    odometer_recorded_at: date | None = None


@dataclass(frozen=True)
class MaintenanceItem:
    title: str
    interval_km: int | None = None
    interval_days: int | None = None
    warning_km: int = 0
    warning_days: int = 0
    last_service_date: date | None = None
    last_service_odometer_km: int | None = None
    enabled: bool = True


@dataclass(frozen=True)
class MaintenanceAssessment:
    title: str
    status: MaintenanceStatus
    remaining_km: int | None = None
    remaining_days: int | None = None


@dataclass(frozen=True)
class ServiceCompleted:
    maintenance_title: str
    serviced_at: date
    odometer_km: int


def complete_service(
    item: MaintenanceItem, serviced_at: date, odometer_km: int
) -> tuple[MaintenanceItem, ServiceCompleted]:
    """Reset only this item's interval baseline and preserve an auditable event."""
    if odometer_km < 0:
        raise ValueError("service odometer cannot be negative")
    updated = MaintenanceItem(
        title=item.title,
        interval_km=item.interval_km,
        interval_days=item.interval_days,
        warning_km=item.warning_km,
        warning_days=item.warning_days,
        last_service_date=serviced_at,
        last_service_odometer_km=odometer_km,
        enabled=item.enabled,
    )
    return updated, ServiceCompleted(item.title, serviced_at, odometer_km)


def assess(
    item: MaintenanceItem,
    motorcycle: MotorcycleState,
    *,
    odometer_stale_after_days: int = 90,
) -> MaintenanceAssessment:
    if not item.enabled:
        return MaintenanceAssessment(item.title, MaintenanceStatus.UNKNOWN)

    mileage_remaining = None
    if item.interval_km is not None:
        if motorcycle.odometer_km is None or item.last_service_odometer_km is None:
            return MaintenanceAssessment(item.title, MaintenanceStatus.UNKNOWN)
        if motorcycle.odometer_recorded_at is not None:
            odometer_age = (
                motorcycle.current_date - motorcycle.odometer_recorded_at
            ).days
            if odometer_age > odometer_stale_after_days:
                return MaintenanceAssessment(item.title, MaintenanceStatus.UNKNOWN)
        mileage_remaining = (
            item.last_service_odometer_km + item.interval_km - motorcycle.odometer_km
        )

    days_remaining = None
    if item.interval_days is not None:
        if item.last_service_date is None:
            return MaintenanceAssessment(item.title, MaintenanceStatus.UNKNOWN)
        due_date = item.last_service_date.fromordinal(
            item.last_service_date.toordinal() + item.interval_days
        )
        days_remaining = (due_date - motorcycle.current_date).days

    if mileage_remaining is None and days_remaining is None:
        return MaintenanceAssessment(item.title, MaintenanceStatus.UNKNOWN)

    remaining_dimensions = [x for x in (mileage_remaining, days_remaining) if x is not None]
    if any(x < 0 for x in remaining_dimensions):
        status = MaintenanceStatus.OVERDUE
    elif any(x == 0 for x in remaining_dimensions):
        status = MaintenanceStatus.DUE
    elif (
        mileage_remaining is not None and mileage_remaining <= item.warning_km
    ) or (days_remaining is not None and days_remaining <= item.warning_days):
        status = MaintenanceStatus.APPROACHING_DUE
    else:
        status = MaintenanceStatus.OK

    return MaintenanceAssessment(item.title, status, mileage_remaining, days_remaining)


_URGENCY = {
    MaintenanceStatus.OVERDUE: 0,
    MaintenanceStatus.DUE: 1,
    MaintenanceStatus.APPROACHING_DUE: 2,
    MaintenanceStatus.OK: 3,
    MaintenanceStatus.UNKNOWN: 4,
}


def next_action(
    items: list[MaintenanceItem],
    motorcycle: MotorcycleState,
    *,
    odometer_stale_after_days: int = 90,
) -> MaintenanceAssessment | None:
    assessments = [
        assess(item, motorcycle, odometer_stale_after_days=odometer_stale_after_days)
        for item in items
        if item.enabled
    ]
    actionable = [
        assessment
        for assessment in assessments
        if assessment.status
        in {
            MaintenanceStatus.OVERDUE,
            MaintenanceStatus.DUE,
            MaintenanceStatus.APPROACHING_DUE,
        }
    ]
    if not actionable:
        return None
    return min(actionable, key=lambda assessment: (_URGENCY[assessment.status], assessment.title))
