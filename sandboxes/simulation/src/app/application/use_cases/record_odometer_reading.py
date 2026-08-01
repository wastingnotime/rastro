from __future__ import annotations

from datetime import date

from app.domain.odometer import OdometerHistory, OdometerReading, record_odometer_reading


class RecordOdometerReading:
    """Owner-facing command for appending a motorcycle odometer reading."""

    def execute(
        self,
        history: OdometerHistory,
        *,
        reading_id: str,
        odometer_km: int,
        recorded_at: date,
        correction_of: str | None = None,
    ) -> tuple[OdometerHistory, OdometerReading]:
        return record_odometer_reading(
            history,
            reading_id,
            odometer_km,
            recorded_at,
            correction_of=correction_of,
        )
