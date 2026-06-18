"""Reusable synthetic port-to-warehouse data generation and scheduling."""

from pathlib import Path
from typing import Any

from .io import write_outputs
from .optimizer import optimize_schedule
from .synthetic import GeneratorConfig, SyntheticDataset, generate_dataset


def generate_and_write(
    config: GeneratorConfig,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Generate data, optimize the schedule, and write the stable CSV contract."""
    dataset = generate_dataset(config)
    schedule, summary = optimize_schedule(dataset.operations, dataset.resources)
    files = write_outputs(Path(output_dir), config, dataset, schedule, summary)
    return {
        "summary": summary,
        "files": files,
        "dataset": dataset,
        "schedule": schedule,
    }


__all__ = [
    "GeneratorConfig",
    "SyntheticDataset",
    "generate_and_write",
    "generate_dataset",
    "optimize_schedule",
]
