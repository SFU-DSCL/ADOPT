from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from . import generate_and_write
from .synthetic import GeneratorConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic port TOS and warehouse WMIS data, then optimize its schedule."
    )
    parser.add_argument("--config", type=Path, help="Optional JSON parameter file")
    parser.add_argument("--ships", type=int)
    parser.add_argument("--containers-per-ship", type=int)
    parser.add_argument("--warehouses", type=int)
    parser.add_argument("--bays-per-warehouse", type=int)
    parser.add_argument("--trucks", type=int)
    parser.add_argument("--terminal-cranes", type=int)
    parser.add_argument("--customer-docks", type=int)
    parser.add_argument("--crossdock-ratio", type=float)
    parser.add_argument("--disruption-rate", type=float)
    parser.add_argument("--horizon-days", type=int)
    parser.add_argument("--start-time")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output-dir", type=Path, default=Path("synthetic-output"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    defaults = asdict(GeneratorConfig())
    if args.config:
        file_parameters = json.loads(args.config.read_text(encoding="utf-8"))
        aliases = {
            "ships": "num_ships",
            "containers_per_ship": "containers_per_ship",
            "warehouses": "num_warehouses",
            "bays_per_warehouse": "bays_per_warehouse",
            "trucks": "num_trucks",
        }
        for key, value in file_parameters.items():
            normalized = aliases.get(key, key)
            if normalized == "start_time":
                value = datetime.fromisoformat(value)
            if normalized in defaults:
                defaults[normalized] = value
    cli_parameters = {
        "num_ships": args.ships,
        "containers_per_ship": args.containers_per_ship,
        "num_warehouses": args.warehouses,
        "bays_per_warehouse": args.bays_per_warehouse,
        "num_trucks": args.trucks,
        "terminal_cranes": args.terminal_cranes,
        "customer_docks": args.customer_docks,
        "crossdock_ratio": args.crossdock_ratio,
        "disruption_rate": args.disruption_rate,
        "horizon_days": args.horizon_days,
        "start_time": datetime.fromisoformat(args.start_time) if args.start_time else None,
        "seed": args.seed,
    }
    defaults.update({key: value for key, value in cli_parameters.items() if value is not None})
    config = GeneratorConfig(**defaults)
    result = generate_and_write(config, args.output_dir)
    summary = result["summary"]
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {len(result['files'])} CSV files to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
