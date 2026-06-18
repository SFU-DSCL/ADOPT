from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Resource:
    resource_id: str
    resource_type: str
    capacity: int
    location_id: str


@dataclass
class Operation:
    operation_id: str
    container_id: str
    operation_type: str
    location_id: str
    resource_id: str
    duration_minutes: int
    release_time: datetime
    due_time: datetime
    dependencies: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScheduledOperation:
    operation_id: str
    container_id: str
    operation_type: str
    location_id: str
    resource_id: str
    planned_start: datetime
    planned_end: datetime
    due_time: datetime
    lateness_minutes: int
    dependencies: tuple[str, ...]
    critical_path_minutes: int

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("planned_start", "planned_end", "due_time"):
            result[key] = result[key].isoformat()
        result["dependencies"] = list(self.dependencies)
        return result
