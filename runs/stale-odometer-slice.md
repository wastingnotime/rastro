# Validation receipt: stale-odometer slice

Date: 2026-07-31

Result: 11 unit tests passed. Mileage-driven assessments now become `unknown`
when the odometer reading is older than the default 90-day freshness window.
The threshold is configurable for scenario exploration, and the runtime
invariant `stale_mileage_is_unknown` passes.
