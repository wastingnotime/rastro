"""Validate the runtime evidence required by the maintenance slice."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from app.simulation.mrl_runtime_scenario import create_simulation
from mrl_simulation_runtime.runner import SimulationRunner


def main() -> None:
    result = SimulationRunner().run(create_simulation())
    observations = [
        json.loads(line)
        for line in result.observations.to_jsonl().splitlines()
        if line.strip()
    ]
    catalog = next(
        observation
        for observation in observations
        if observation["type"] == "use_case_catalog"
    )
    catalog_ids = {
        use_case["use_case_id"] for use_case in catalog["payload"]["use_cases"]
    }
    required_ids = {
        "customize-warning-thresholds",
        "restore-manufacturer-warning-thresholds",
        "view-warning-threshold-history",
    }
    if not required_ids <= catalog_ids:
        raise AssertionError("threshold use cases are missing from the runtime catalog")

    executions = [
        observation
        for observation in observations
        if observation["type"] == "use_case_executed"
    ]
    for use_case_id in required_ids:
        if not any(
            observation["payload"]["use_case_id"] == use_case_id
            and observation["payload"]["outcome"] == "succeeded"
            for observation in executions
        ):
            raise AssertionError(f"missing successful execution: {use_case_id}")
    if not any(
        observation["payload"].get("code") == "warning_threshold_history_forbidden"
        and observation["payload"]["outcome"] == "rejected"
        for observation in executions
    ):
        raise AssertionError("missing forbidden threshold-history execution")

    summaries = [
        observation
        for observation in observations
        if observation["type"] == "use_case_summary"
        and observation["name"] == "owner-start"
    ]
    if len(summaries) != 1 or summaries[0]["payload"]["execution_count"] < 10:
        raise AssertionError("owner-start use-case summary is incomplete")

    owner_status_responses = [
        observation
        for observation in observations
        if observation["type"] == "owner_status_api_response"
    ]
    if not any(
        response["payload"].get("status_code") == 200
        and response["payload"].get("schema_version") == 1
        for response in owner_status_responses
    ):
        raise AssertionError("missing successful owner-status API response")
    if not any(
        response["payload"].get("status_code") == 403
        and response["payload"].get("attention_exposed") is False
        for response in owner_status_responses
    ):
        raise AssertionError("missing forbidden owner-status API response")

    reminder_evaluations = [
        observation
        for observation in observations
        if observation["type"] == "reminder_evaluation"
    ]
    if not reminder_evaluations:
        raise AssertionError("missing reminder evaluation")
    reminder_payload = reminder_evaluations[0]["payload"]
    if not reminder_payload["first_reminders"] or reminder_payload["next_day_reminders"]:
        raise AssertionError("reminder cadence evidence is incomplete")

    profiles = {
        observation["name"]: observation
        for observation in observations
        if observation["type"] == "profile_evidence"
    }
    if set(profiles) != {"daily_commuter", "weekend_rider", "long_unused"}:
        raise AssertionError("ownership profile evidence is incomplete")
    if profiles["long_unused"]["payload"]["unknown_days"] != 274:
        raise AssertionError("long-unused freshness evidence is unexpected")
    reminder_profiles = {
        observation["name"]
        for observation in observations
        if observation["type"] == "reminder_profile_evidence"
    }
    expected_reminder_profiles = {
        f"{profile}_{cadence}d"
        for profile in profiles
        for cadence in (7, 14, 30)
    }
    if reminder_profiles != expected_reminder_profiles:
        raise AssertionError("reminder profile evidence is incomplete")

    threshold_sequence = [
        observation
        for observation in observations
        if observation["name"]
        in {
            "CustomizeWarningThresholds",
            "warning_thresholds_customized",
            "RestoreManufacturerWarningThresholds",
            "warning_thresholds_restored",
            "ViewWarningThresholdHistory",
        }
        and observation["type"] in {"use_case_executed", "domain_event"}
    ]
    threshold_times = [
        datetime.fromisoformat(observation["sim_time"])
        for observation in threshold_sequence
    ]
    if threshold_times != sorted(threshold_times) or len(set(threshold_times)) == 1:
        raise AssertionError("threshold interactions are not temporally ordered")
    if any(
        later - earlier < timedelta(seconds=2)
        for earlier, later in zip(threshold_times, threshold_times[1:])
    ):
        raise AssertionError("threshold phases are closer than the configured interval")
    print(
        "validated runtime evidence: "
        f"{len(observations)} observations, "
        f"{summaries[0]['payload']['execution_count']} owner-start executions"
    )


if __name__ == "__main__":
    main()
