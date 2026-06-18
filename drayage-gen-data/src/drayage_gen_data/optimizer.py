from __future__ import annotations

import heapq
from collections import defaultdict
from datetime import datetime, timedelta

from .models import Operation, Resource, ScheduledOperation


class ResourceCalendar:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.intervals: list[tuple[datetime, datetime, str]] = []

    def _fits(self, start: datetime, end: datetime) -> bool:
        points: list[tuple[datetime, int]] = [(start, 1), (end, -1)]
        for existing_start, existing_end, _ in self.intervals:
            if existing_start < end and existing_end > start:
                points.append((max(start, existing_start), 1))
                points.append((min(end, existing_end), -1))
        active = 0
        for _, delta in sorted(points, key=lambda point: (point[0], point[1])):
            active += delta
            if active > self.capacity:
                return False
        return True

    def reserve(self, earliest: datetime, duration_minutes: int, operation_id: str) -> tuple[datetime, datetime]:
        candidate = earliest
        duration = timedelta(minutes=duration_minutes)
        while True:
            end = candidate + duration
            if self._fits(candidate, end):
                self.intervals.append((candidate, end, operation_id))
                return candidate, end
            next_times = [
                existing_end
                for existing_start, existing_end, _ in self.intervals
                if existing_start < end and existing_end > candidate and existing_end > candidate
            ]
            if not next_times:
                raise RuntimeError(f"Unable to find a resource slot for {operation_id}")
            candidate = min(next_times)


def _topological_order(operations: dict[str, Operation]) -> tuple[list[str], dict[str, list[str]]]:
    children: dict[str, list[str]] = defaultdict(list)
    indegree = {operation_id: 0 for operation_id in operations}
    for operation in operations.values():
        for dependency in operation.dependencies:
            if dependency not in operations:
                raise ValueError(f"{operation.operation_id} depends on missing operation {dependency}")
            children[dependency].append(operation.operation_id)
            indegree[operation.operation_id] += 1
    ready = [operation_id for operation_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        current = heapq.heappop(ready)
        order.append(current)
        for child in children[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, child)
    if len(order) != len(operations):
        raise ValueError("Operation dependency graph contains a cycle")
    return order, children


def _critical_path_minutes(
    operations: dict[str, Operation],
    order: list[str],
    children: dict[str, list[str]],
) -> dict[str, int]:
    critical: dict[str, int] = {}
    for operation_id in reversed(order):
        operation = operations[operation_id]
        critical[operation_id] = operation.duration_minutes + max(
            (critical[child] for child in children[operation_id]),
            default=0,
        )
    return critical


def optimize_schedule(
    operation_list: list[Operation],
    resource_list: list[Resource],
) -> tuple[list[ScheduledOperation], dict]:
    operations = {operation.operation_id: operation for operation in operation_list}
    if len(operations) != len(operation_list):
        raise ValueError("Operation IDs must be unique")
    resources = {resource.resource_id: resource for resource in resource_list}
    order, children = _topological_order(operations)
    critical = _critical_path_minutes(operations, order, children)
    calendars = {
        resource_id: ResourceCalendar(resource.capacity)
        for resource_id, resource in resources.items()
    }
    remaining_dependencies = {
        operation_id: len(operation.dependencies)
        for operation_id, operation in operations.items()
    }
    ready: list[tuple[int, datetime, str]] = []
    for operation_id, count in remaining_dependencies.items():
        if count == 0:
            operation = operations[operation_id]
            heapq.heappush(ready, (-critical[operation_id], operation.due_time, operation_id))

    end_times: dict[str, datetime] = {}
    scheduled: list[ScheduledOperation] = []
    while ready:
        _, _, operation_id = heapq.heappop(ready)
        operation = operations[operation_id]
        if operation.resource_id not in calendars:
            raise ValueError(
                f"{operation.operation_id} references missing resource {operation.resource_id}"
            )
        predecessor_end = max(
            (end_times[dependency] for dependency in operation.dependencies),
            default=operation.release_time,
        )
        earliest = max(operation.release_time, predecessor_end)
        start, end = calendars[operation.resource_id].reserve(
            earliest, operation.duration_minutes, operation_id
        )
        end_times[operation_id] = end
        lateness = max(0, round((end - operation.due_time).total_seconds() / 60))
        scheduled.append(
            ScheduledOperation(
                operation_id=operation_id,
                container_id=operation.container_id,
                operation_type=operation.operation_type,
                location_id=operation.location_id,
                resource_id=operation.resource_id,
                planned_start=start,
                planned_end=end,
                due_time=operation.due_time,
                lateness_minutes=lateness,
                dependencies=tuple(operation.dependencies),
                critical_path_minutes=critical[operation_id],
            )
        )
        for child in children[operation_id]:
            remaining_dependencies[child] -= 1
            if remaining_dependencies[child] == 0:
                child_operation = operations[child]
                heapq.heappush(
                    ready,
                    (-critical[child], child_operation.due_time, child),
                )

    if len(scheduled) != len(operation_list):
        raise RuntimeError("Not all operations were scheduled")
    scheduled.sort(key=lambda operation: (operation.planned_start, operation.operation_id))
    delivery_operations = [
        operation for operation in scheduled if operation.operation_type == "customer_delivery"
    ]
    late_deliveries = [operation for operation in delivery_operations if operation.lateness_minutes]
    makespan_start = min(operation.planned_start for operation in scheduled)
    makespan_end = max(operation.planned_end for operation in scheduled)
    summary = {
        "operation_count": len(scheduled),
        "container_count": len({operation.container_id for operation in scheduled}),
        "delivery_count": len(delivery_operations),
        "late_delivery_count": len(late_deliveries),
        "on_time_delivery_pct": round(
            100 * (len(delivery_operations) - len(late_deliveries)) / len(delivery_operations),
            2,
        ) if delivery_operations else 100.0,
        "total_lateness_minutes": sum(operation.lateness_minutes for operation in late_deliveries),
        "makespan_start": makespan_start.isoformat(),
        "makespan_end": makespan_end.isoformat(),
        "makespan_hours": round((makespan_end - makespan_start).total_seconds() / 3600, 2),
        "graph_node_count": len(operations),
        "graph_edge_count": sum(len(operation.dependencies) for operation in operations.values()),
    }
    return scheduled, summary
