"""Run the first slice and write its semantic observation log to stdout."""

from app.simulation.mrl_runtime_scenario import create_simulation
from mrl_simulation_runtime.runner import SimulationRunner


if __name__ == "__main__":
    print(SimulationRunner().run(create_simulation()).observations.to_jsonl(), end="")
