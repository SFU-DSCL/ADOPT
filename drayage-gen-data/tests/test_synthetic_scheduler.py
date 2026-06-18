from __future__ import annotations

import tempfile
import unittest
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from drayage_gen_data import generate_and_write
from drayage_gen_data.io import CSV_OUTPUT_FILES, write_outputs
from drayage_gen_data.optimizer import optimize_schedule
from drayage_gen_data.synthetic import GeneratorConfig, generate_dataset


class SyntheticSchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = GeneratorConfig(
            num_ships=2,
            containers_per_ship=6,
            num_warehouses=2,
            bays_per_warehouse=6,
            num_trucks=4,
            terminal_cranes=2,
            customer_docks=2,
            crossdock_ratio=0.5,
            start_time=datetime(2026, 6, 8, 6, 0),
            seed=11,
        )
        self.dataset = generate_dataset(self.config)
        self.schedule, self.summary = optimize_schedule(
            self.dataset.operations,
            self.dataset.resources,
        )

    def test_expected_record_counts(self) -> None:
        container_count = self.config.num_ships * self.config.containers_per_ship
        self.assertEqual(len(self.dataset.vessel_calls), self.config.num_ships)
        self.assertEqual(len(self.dataset.containers), container_count)
        self.assertEqual(len(self.dataset.warehouse_orders), container_count)
        self.assertEqual(len(self.dataset.operations), container_count * 8)
        self.assertEqual(len(self.schedule), container_count * 8)

    def test_dependencies_finish_before_children_start(self) -> None:
        by_id = {operation.operation_id: operation for operation in self.schedule}
        for operation in self.schedule:
            for dependency in operation.dependencies:
                self.assertLessEqual(by_id[dependency].planned_end, operation.planned_start)

    def test_resource_capacities_are_not_exceeded(self) -> None:
        capacities = {
            resource.resource_id: resource.capacity
            for resource in self.dataset.resources
        }
        by_resource = defaultdict(list)
        for operation in self.schedule:
            by_resource[operation.resource_id].append(operation)
        for resource_id, operations in by_resource.items():
            points = []
            for operation in operations:
                points.append((operation.planned_start, 1))
                points.append((operation.planned_end, -1))
            active = 0
            for _, delta in sorted(points, key=lambda point: (point[0], point[1])):
                active += delta
                self.assertLessEqual(active, capacities[resource_id])

    def test_run_summary_matches_graph(self) -> None:
        self.assertEqual(self.summary["container_count"], 12)
        self.assertEqual(self.summary["graph_node_count"], 96)
        self.assertEqual(self.summary["graph_edge_count"], 84)

    def test_output_writer_handles_sparse_event_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = write_outputs(
                Path(directory),
                self.config,
                self.dataset,
                self.schedule,
                self.summary,
            )
            self.assertEqual(set(manifest), set(CSV_OUTPUT_FILES))
            for relative_path in CSV_OUTPUT_FILES:
                self.assertTrue((Path(directory) / relative_path).exists())

    def test_public_api_generates_all_csv_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = generate_and_write(self.config, Path(directory))
            self.assertEqual(result["summary"]["container_count"], 12)
            self.assertEqual(set(result["files"]), set(CSV_OUTPUT_FILES))


if __name__ == "__main__":
    unittest.main()
