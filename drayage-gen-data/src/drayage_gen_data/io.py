from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .models import Operation, Resource, ScheduledOperation
from .synthetic import GeneratorConfig, SyntheticDataset

CSV_SCHEMAS: dict[str, list[str]] = {
    "tos/vessel_calls.csv": [
        "vessel_call_id", "vessel_name", "voyage", "terminal_id", "eta", "berth_start",
        "berth_end", "berth_delay_minutes", "container_count",
    ],
    "tos/containers.csv": [
        "container_id", "vessel_call_id", "terminal_id", "warehouse_id", "commodity",
        "size_teu", "gross_weight_kg", "crossdock_required", "available_time", "delivery_due",
    ],
    "tos/events.csv": [
        "timestamp", "event_type", "entity_id", "source_system", "value", "unit",
    ],
    "wmis/warehouses.csv": [
        "warehouse_id", "name", "receiving_bays", "crossdock_bays", "outbound_bays",
        "total_bays", "storage_positions",
    ],
    "wmis/warehouse_orders.csv": [
        "order_id", "container_id", "warehouse_id", "order_type", "commodity", "units",
        "customer_id", "delivery_due",
    ],
    "wmis/warehouse_tasks.csv": [
        "operation_id", "container_id", "operation_type", "location_id", "resource_id",
        "duration_minutes", "release_time", "due_time", "dependencies", "attributes",
    ],
    "optimizer/resources.csv": [
        "resource_id", "resource_type", "capacity", "location_id",
    ],
    "optimizer/operations.csv": [
        "operation_id", "container_id", "operation_type", "location_id", "resource_id",
        "duration_minutes", "release_time", "due_time", "dependencies", "attributes",
    ],
    "optimizer/graph_nodes.csv": [
        "operation_id", "container_id", "operation_type", "location_id", "resource_id",
    ],
    "optimizer/graph_edges.csv": [
        "source_operation_id", "target_operation_id",
    ],
    "optimizer/optimized_schedule.csv": [
        "operation_id", "container_id", "operation_type", "location_id", "resource_id",
        "planned_start", "planned_end", "due_time", "lateness_minutes", "dependencies",
        "critical_path_minutes",
    ],
    "run_parameters.csv": ["parameter", "value"],
    "run_summary.csv": ["metric", "value"],
    "file_manifest.csv": ["dataset", "relative_path", "row_count"],
}
CSV_OUTPUT_FILES = tuple(CSV_SCHEMAS)


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return json.dumps(value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return value


def _write_csv(
    path: Path,
    rows: Iterable[dict[str, Any]],
    fieldnames: list[str],
) -> int:
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: _serialize(row.get(key, ""))
                for key in fieldnames
            })
    return len(rows)


def operation_to_dict(operation: Operation) -> dict[str, Any]:
    row = asdict(operation)
    row["release_time"] = operation.release_time.isoformat()
    row["due_time"] = operation.due_time.isoformat()
    return row


def write_outputs(
    output_dir: Path,
    config: GeneratorConfig,
    dataset: SyntheticDataset,
    schedule: list[ScheduledOperation],
    summary: dict[str, Any],
) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    tos_dir = output_dir / "tos"
    wmis_dir = output_dir / "wmis"
    optimizer_dir = output_dir / "optimizer"
    for directory in (tos_dir, wmis_dir, optimizer_dir):
        directory.mkdir(exist_ok=True)

    rows: dict[str, list[dict[str, Any]]] = {
        "tos/vessel_calls.csv": dataset.vessel_calls,
        "tos/containers.csv": dataset.containers,
        "tos/events.csv": dataset.events,
        "wmis/warehouses.csv": dataset.warehouses,
        "wmis/warehouse_orders.csv": dataset.warehouse_orders,
        "wmis/warehouse_tasks.csv": [
            operation_to_dict(operation)
            for operation in dataset.operations
            if operation.operation_type.startswith("warehouse_")
        ],
        "optimizer/resources.csv": [asdict(resource) for resource in dataset.resources],
        "optimizer/operations.csv": [
            operation_to_dict(operation) for operation in dataset.operations
        ],
        "optimizer/graph_nodes.csv": [
            {
                "operation_id": operation.operation_id,
                "container_id": operation.container_id,
                "operation_type": operation.operation_type,
                "location_id": operation.location_id,
                "resource_id": operation.resource_id,
            }
            for operation in dataset.operations
        ],
        "optimizer/graph_edges.csv": [
            {
                "source_operation_id": dependency,
                "target_operation_id": operation.operation_id,
            }
            for operation in dataset.operations
            for dependency in operation.dependencies
        ],
        "optimizer/optimized_schedule.csv": [
            operation.to_dict() for operation in schedule
        ],
        "run_parameters.csv": [
            {"parameter": key, "value": _serialize(value)}
            for key, value in asdict(config).items()
        ],
        "run_summary.csv": [
            {"metric": key, "value": value}
            for key, value in summary.items()
        ],
    }
    row_counts = {
        relative_path: _write_csv(
            output_dir / relative_path,
            file_rows,
            CSV_SCHEMAS[relative_path],
        )
        for relative_path, file_rows in rows.items()
    }
    manifest_rows = [
        {
            "dataset": relative_path.rsplit("/", 1)[0] if "/" in relative_path else "run",
            "relative_path": relative_path,
            "row_count": row_count,
        }
        for relative_path, row_count in row_counts.items()
    ]
    row_counts["file_manifest.csv"] = _write_csv(
        output_dir / "file_manifest.csv",
        manifest_rows,
        CSV_SCHEMAS["file_manifest.csv"],
    )
    return row_counts
