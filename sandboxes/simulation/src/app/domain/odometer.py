from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class OdometerReading:
    reading_id: str
    value_km: int
    recorded_at: date
    note: str | None = None
    correction_of: str | None = None


@dataclass(frozen=True)
class OdometerHistory:
    readings: tuple[OdometerReading, ...] = ()


def record_odometer_reading(
    history: OdometerHistory,
    reading_id: str,
    value_km: int,
    recorded_at: date,
    *,
    note: str | None = None,
    correction_of: str | None = None,
) -> tuple[OdometerHistory, OdometerReading]:
    if not reading_id.strip():
        raise ValueError("reading id is required")
    if any(reading.reading_id == reading_id for reading in history.readings):
        raise ValueError("reading id already exists")
    if value_km < 0:
        raise ValueError("odometer reading cannot be negative")
    if correction_of is not None:
        if not any(reading.reading_id == correction_of for reading in history.readings):
            raise ValueError("corrected reading was not found")
        if any(reading.correction_of == correction_of for reading in history.readings):
            raise ValueError("reading has already been corrected")
    else:
        current = current_odometer_reading(history)
        if current is not None and value_km < current.value_km:
            raise ValueError("odometer readings cannot decrease without correction")
    reading = OdometerReading(
        reading_id,
        value_km,
        recorded_at,
        note=note,
        correction_of=correction_of,
    )
    return OdometerHistory(history.readings + (reading,)), reading


def current_odometer_reading(history: OdometerHistory) -> OdometerReading | None:
    corrected_ids = {
        reading.correction_of
        for reading in history.readings
        if reading.correction_of is not None
    }
    valid = [
        reading
        for reading in history.readings
        if reading.reading_id not in corrected_ids
    ]
    if not valid:
        return None
    return max(valid, key=lambda reading: (reading.recorded_at, reading.reading_id))
