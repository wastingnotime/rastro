# MRL build receipt: use-case observatory graph

Date: 2026-08-01

## Change

Added six first-class `use_case` nodes to the MRL scenario observatory graph,
one for each catalog definition. Each node includes its query/command realm
and purpose, with an owner→use-case `invokes` edge.

## Validation

```text
use_case nodes: 6
use_case edges: 6
Ran 70 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18781 --once
listening on http://127.0.0.1:18781
```
