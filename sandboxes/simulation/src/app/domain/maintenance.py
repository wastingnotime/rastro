from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum


class MaintenanceStatus(str, Enum):
    OK = "ok"
    APPROACHING_DUE = "approaching_due"
    DUE = "due"
    OVERDUE = "overdue"
    UNKNOWN = "unknown"


class ThresholdSource(str, Enum):
    MANUFACTURER = "manufacturer"
    OWNER = "owner"
    MIXED = "mixed"


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
    warning_km_source: ThresholdSource = ThresholdSource.MANUFACTURER
    warning_days_source: ThresholdSource = ThresholdSource.MANUFACTURER

    @property
    def warning_source(self) -> ThresholdSource:
        if self.warning_km_source == self.warning_days_source:
            return self.warning_km_source
        return ThresholdSource.MIXED


@dataclass(frozen=True)
class MaintenanceAssessment:
    title: str
    status: MaintenanceStatus
    remaining_km: int | None = None
    remaining_days: int | None = None
    warning_source: ThresholdSource = ThresholdSource.MANUFACTURER


@dataclass(frozen=True)
class AttentionGroup:
    status: MaintenanceStatus
    items: tuple[MaintenanceAssessment, ...]


@dataclass(frozen=True)
class ServiceCompleted:
    maintenance_title: str
    serviced_at: date
    odometer_km: int


@dataclass(frozen=True)
class ServiceRecorded:
    serviced_at: date
    odometer_km: int
    completed_titles: tuple[str, ...]
    provider_name: str | None = None
    notes: str | None = None
    service_id: str = "service-record"


@dataclass(frozen=True)
class ServiceRecordVoided:
    service_id: str
    reason: str


@dataclass(frozen=True)
class WarningThresholdsCustomized:
    maintenance_title: str
    previous_warning_km: int
    previous_warning_days: int
    warning_km: int
    warning_days: int


def customize_warning_thresholds(
    item: MaintenanceItem,
    *,
    warning_km: int | None = None,
    warning_days: int | None = None,
) -> MaintenanceItem:
    """Apply owner warning preferences while retaining explicit provenance."""
    if warning_km is None and warning_days is None:
        raise ValueError("at least one warning threshold is required")
    if warning_km is not None and warning_km < 0:
        raise ValueError("warning mileage cannot be negative")
    if warning_days is not None and warning_days < 0:
        raise ValueError("warning days cannot be negative")
    return replace(
        item,
        warning_km=item.warning_km if warning_km is None else warning_km,
        warning_days=item.warning_days if warning_days is None else warning_days,
        warning_km_source=(
            item.warning_km_source if warning_km is None else ThresholdSource.OWNER
        ),
        warning_days_source=(
            item.warning_days_source if warning_days is None else ThresholdSource.OWNER
        ),
    )


def customize_warning_thresholds_with_event(
    item: MaintenanceItem,
    *,
    warning_km: int | None = None,
    warning_days: int | None = None,
) -> tuple[MaintenanceItem, WarningThresholdsCustomized]:
    """Apply owner thresholds and preserve the before/after audit event."""
    updated = customize_warning_thresholds(
        item,
        warning_km=warning_km,
        warning_days=warning_days,
    )
    event = WarningThresholdsCustomized(
        maintenance_title=item.title,
        previous_warning_km=item.warning_km,
        previous_warning_days=item.warning_days,
        warning_km=updated.warning_km,
        warning_days=updated.warning_days,
    )
    return updated, event


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
        warning_km_source=item.warning_km_source,
        warning_days_source=item.warning_days_source,
    )
    return updated, ServiceCompleted(item.title, serviced_at, odometer_km)


def record_service(
    items: list[MaintenanceItem],
    completed_titles: list[str],
    serviced_at: date,
    odometer_km: int,
    *,
    provider_name: str | None = None,
    notes: str | None = None,
    service_id: str = "service-record",
) -> tuple[list[MaintenanceItem], ServiceRecorded]:
    """Apply one auditable service visit to a selected subset of items."""
    if odometer_km < 0:
        raise ValueError("service odometer cannot be negative")
    if len(set(completed_titles)) != len(completed_titles):
        raise ValueError("service items cannot be duplicated")
    by_title = {item.title: item for item in items}
    missing = [title for title in completed_titles if title not in by_title]
    if missing:
        raise ValueError(f"unknown maintenance items: {', '.join(missing)}")
    selected = set(completed_titles)
    updated = [
        complete_service(item, serviced_at, odometer_km)[0]
        if item.title in selected
        else item
        for item in items
    ]
    event = ServiceRecorded(
        serviced_at=serviced_at,
        odometer_km=odometer_km,
        completed_titles=tuple(completed_titles),
        provider_name=provider_name,
        notes=notes,
        service_id=service_id,
    )
    return updated, event


def void_service_record(service_id: str, reason: str) -> ServiceRecordVoided:
    if not service_id.strip():
        raise ValueError("service id is required")
    if not reason.strip():
        raise ValueError("void reason is required")
    return ServiceRecordVoided(service_id, reason)


def project_service_history(
    items: list[MaintenanceItem],
    records: list[ServiceRecorded],
    voided_records: list[ServiceRecordVoided] | None = None,
) -> list[MaintenanceItem]:
    """Rebuild baselines from active records without deleting audit events."""
    voided_ids = {event.service_id for event in (voided_records or [])}
    active_records = [record for record in records if record.service_id not in voided_ids]
    projected = list(items)
    for index, item in enumerate(items):
        matching = [record for record in active_records if item.title in record.completed_titles]
        if matching:
            record = max(matching, key=lambda value: (value.serviced_at, value.service_id))
            projected[index] = complete_service(item, record.serviced_at, record.odometer_km)[0]
    return projected


def assess(
    item: MaintenanceItem,
    motorcycle: MotorcycleState,
    *,
    odometer_stale_after_days: int = 90,
) -> MaintenanceAssessment:
    if not item.enabled:
        return MaintenanceAssessment(
            item.title, MaintenanceStatus.UNKNOWN, warning_source=item.warning_source
        )

    mileage_remaining = None
    if item.interval_km is not None:
        if motorcycle.odometer_km is None or item.last_service_odometer_km is None:
            return MaintenanceAssessment(
                item.title, MaintenanceStatus.UNKNOWN, warning_source=item.warning_source
            )
        if motorcycle.odometer_recorded_at is not None:
            odometer_age = (
                motorcycle.current_date - motorcycle.odometer_recorded_at
            ).days
            if odometer_age > odometer_stale_after_days:
                return MaintenanceAssessment(
                    item.title, MaintenanceStatus.UNKNOWN, warning_source=item.warning_source
                )
        mileage_remaining = (
            item.last_service_odometer_km + item.interval_km - motorcycle.odometer_km
        )

    days_remaining = None
    if item.interval_days is not None:
        if item.last_service_date is None:
            return MaintenanceAssessment(
                item.title, MaintenanceStatus.UNKNOWN, warning_source=item.warning_source
            )
        due_date = item.last_service_date.fromordinal(
            item.last_service_date.toordinal() + item.interval_days
        )
        days_remaining = (due_date - motorcycle.current_date).days

    if mileage_remaining is None and days_remaining is None:
        return MaintenanceAssessment(
            item.title, MaintenanceStatus.UNKNOWN, warning_source=item.warning_source
        )

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

    return MaintenanceAssessment(
        item.title,
        status,
        mileage_remaining,
        days_remaining,
        item.warning_source,
    )


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
    actions = next_actions(
        items,
        motorcycle,
        odometer_stale_after_days=odometer_stale_after_days,
    )
    return actions[0] if actions else None


def next_actions(
    items: list[MaintenanceItem],
    motorcycle: MotorcycleState,
    *,
    odometer_stale_after_days: int = 90,
) -> list[MaintenanceAssessment]:
    """Return the highest-urgency group for the primary owner action."""
    groups = grouped_actions(
        items,
        motorcycle,
        odometer_stale_after_days=odometer_stale_after_days,
    )
    return list(groups[0].items) if groups else []


def grouped_actions(
    items: list[MaintenanceItem],
    motorcycle: MotorcycleState,
    *,
    odometer_stale_after_days: int = 90,
) -> list[AttentionGroup]:
    """Return every actionable urgency group, highest urgency first."""
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
        return []
    by_status: dict[MaintenanceStatus, list[MaintenanceAssessment]] = {}
    for assessment in actionable:
        by_status.setdefault(assessment.status, []).append(assessment)
    return [
        AttentionGroup(
            status,
            tuple(sorted(by_status[status], key=lambda assessment: assessment.title)),
        )
        for status in sorted(by_status, key=lambda value: _URGENCY[value])
    ]
