# drayage-gen-data

Generate synthetic port Terminal Operating System (TOS) and warehouse WMIS datasets, construct a
directed dependency graph, and create a capacity-feasible drayage schedule.

The project uses only the Python standard library.

## Quick Start

Run directly from the project without installing anything:

```bash
cd drayage-gen-data
python3 generate.py \
  --config examples/config.json \
  --output-dir generated-data/example
```

Or install it as an editable command:

```bash
python3 -m pip install -e .
drayage-gen-data \
  --config examples/config.json \
  --output-dir generated-data/example
```

Command-line arguments override values from the JSON configuration:

```bash
python3 generate.py \
  --ships 4 \
  --containers-per-ship 100 \
  --warehouses 3 \
  --bays-per-warehouse 12 \
  --trucks 30 \
  --terminal-cranes 4 \
  --customer-docks 10 \
  --crossdock-ratio 0.55 \
  --disruption-rate 0.2 \
  --seed 27 \
  --output-dir generated-data/large-run
```

## Parameters

| Parameter | Meaning |
| --- | --- |
| `ships` | Number of vessel calls |
| `containers_per_ship` | Import containers discharged per vessel |
| `warehouses` | Number of warehouse facilities |
| `bays_per_warehouse` | Receiving, cross-dock, and outbound bays per warehouse |
| `trucks` | Concurrent drayage truck capacity |
| `terminal_cranes` | Concurrent terminal crane capacity |
| `customer_docks` | Concurrent destination unloading capacity |
| `crossdock_ratio` | Share of containers routed through cross-docking |
| `disruption_rate` | Probability of a vessel berth delay |
| `horizon_days` | Maximum generated delivery horizon |
| `start_time` | ISO-8601 simulation start |
| `seed` | Deterministic random seed |

## Generated Data

```text
generated-data/example/
  file_manifest.csv
  run_parameters.csv
  run_summary.csv
  tos/
    vessel_calls.csv
    containers.csv
    events.csv
  wmis/
    warehouses.csv
    warehouse_orders.csv
    warehouse_tasks.csv
  optimizer/
    resources.csv
    operations.csv
    graph_nodes.csv
    graph_edges.csv
    optimized_schedule.csv
```

Each container creates the following graph:

```text
terminal discharge
  -> terminal gate ready
  -> import drayage
  -> warehouse receive
  -> cross-dock or storage pick
  -> warehouse outbound
  -> delivery drayage
  -> customer delivery
```

## Scheduling Algorithm

The optimizer:

1. Validates the graph and calculates a topological order.
2. Calculates each operation's reverse critical-path duration.
3. Prioritizes ready operations by critical-path length and due date.
4. Finds the earliest feasible slot for the required resource.
5. Enforces crane, truck, warehouse-bay, and customer-dock capacities.
6. Reports delivery lateness, makespan, node count, and edge count.

Every output is CSV with a stable, explicit column schema. `file_manifest.csv` lists each dataset
and its row count. See [`CSV_CONTRACT.md`](CSV_CONTRACT.md) for the integration contract.

## Python API

```python
from pathlib import Path

from drayage_gen_data import GeneratorConfig, generate_and_write

result = generate_and_write(
    GeneratorConfig(
        num_ships=4,
        containers_per_ship=100,
        num_warehouses=3,
        seed=27,
    ),
    Path("generated-data/run-27"),
)

print(result["summary"])
print(result["files"])
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Reusing In Another Project

Choose either integration:

1. Copy or clone this repository and invoke `python3 generate.py`.
2. Install the package with `pip install .` and use the `drayage-gen-data` command or Python API.

The generator has no runtime dependencies outside the Python standard library.
