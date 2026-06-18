# CSV Output Contract

All files are UTF-8 CSV with a header row. Timestamps use ISO-8601 local datetime strings.
List and object fields inside a cell use JSON encoding.

## TOS

- `tos/vessel_calls.csv`: vessel arrival, berth, voyage, delay, and container-count records.
- `tos/containers.csv`: container routing, cargo, availability, and delivery-due records.
- `tos/events.csv`: time-series TOS events and disruptions.

## WMIS

- `wmis/warehouses.csv`: facility and bay-capacity master data.
- `wmis/warehouse_orders.csv`: inbound order, customer, commodity, and flow-type data.
- `wmis/warehouse_tasks.csv`: receiving, cross-dock/storage-pick, and outbound tasks.

## Graph And Schedule

- `optimizer/resources.csv`: resource types and concurrent capacities.
- `optimizer/operations.csv`: all terminal-to-customer graph operations.
- `optimizer/graph_nodes.csv`: graph-node projection for each operation.
- `optimizer/graph_edges.csv`: predecessor-to-successor dependency edges.
- `optimizer/optimized_schedule.csv`: capacity-feasible planned start/end times and lateness.

## Run Metadata

- `run_parameters.csv`: generation inputs used for the run.
- `run_summary.csv`: schedule and graph performance metrics.
- `file_manifest.csv`: relative output path and row count for every generated dataset.

The exact ordered columns are defined by `CSV_SCHEMAS` in
`src/drayage_gen_data/io.py`. New columns should be appended rather than reordered or renamed.
