"""Validate the runtime evidence required by the maintenance slice."""

from __future__ import annotations

import json

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
    print(
        "validated runtime evidence: "
        f"{len(observations)} observations, "
        f"{summaries[0]['payload']['execution_count']} owner-start executions"
    )


if __name__ == "__main__":
    main()
