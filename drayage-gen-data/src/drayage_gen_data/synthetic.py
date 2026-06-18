from __future__ import annotations

import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import Operation, Resource


@dataclass(frozen=True)
class GeneratorConfig:
    num_ships: int = 3
    containers_per_ship: int = 40
    num_warehouses: int = 2
    bays_per_warehouse: int = 8
    num_trucks: int = 18
    terminal_cranes: int = 3
    customer_docks: int = 6
    crossdock_ratio: float = 0.45
    disruption_rate: float = 0.12
    horizon_days: int = 5
    start_time: datetime = datetime(2026, 6, 8, 6, 0)
    seed: int = 42

    def validate(self) -> None:
        integer_fields = {
            "num_ships": self.num_ships,
            "containers_per_ship": self.containers_per_ship,
            "num_warehouses": self.num_warehouses,
            "bays_per_warehouse": self.bays_per_warehouse,
            "num_trucks": self.num_trucks,
            "terminal_cranes": self.terminal_cranes,
            "customer_docks": self.customer_docks,
            "horizon_days": self.horizon_days,
        }
        for name, value in integer_fields.items():
            if value < 1:
                raise ValueError(f"{name} must be at least 1")
        for name, value in {
            "crossdock_ratio": self.crossdock_ratio,
            "disruption_rate": self.disruption_rate,
        }.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass
class SyntheticDataset:
    vessel_calls: list[dict]
    containers: list[dict]
    warehouses: list[dict]
    warehouse_orders: list[dict]
    events: list[dict]
    resources: list[Resource]
    operations: list[Operation]


def _container_number(rng: random.Random, sequence: int) -> str:
    owner = "".join(rng.choice(string.ascii_uppercase) for _ in range(3)) + "U"
    return f"{owner}{sequence:07d}"


def _warehouse_bay_split(total_bays: int) -> tuple[int, int, int]:
    receiving = max(1, round(total_bays * 0.5))
    crossdock = max(1, round(total_bays * 0.25))
    outbound = max(1, total_bays - receiving - crossdock)
    while receiving + crossdock + outbound > total_bays:
        receiving = max(1, receiving - 1)
    return receiving, crossdock, outbound


def generate_dataset(config: GeneratorConfig) -> SyntheticDataset:
    config.validate()
    rng = random.Random(config.seed)
    terminal_id = "PORT-MARIEN"
    resources = [
        Resource("TERMINAL_CRANES", "terminal_crane", config.terminal_cranes, terminal_id),
        Resource("DRAYAGE_TRUCKS", "truck", config.num_trucks, "NETWORK"),
        Resource("CUSTOMER_DOCKS", "customer_dock", config.customer_docks, "CUSTOMER-NETWORK"),
    ]
    warehouses: list[dict] = []
    for index in range(config.num_warehouses):
        warehouse_id = f"WH-{index + 1:02d}"
        receiving, crossdock, outbound = _warehouse_bay_split(config.bays_per_warehouse)
        warehouses.append(
            {
                "warehouse_id": warehouse_id,
                "name": f"NorthPort Warehouse {index + 1}",
                "receiving_bays": receiving,
                "crossdock_bays": crossdock,
                "outbound_bays": outbound,
                "total_bays": config.bays_per_warehouse,
                "storage_positions": config.bays_per_warehouse * 450,
            }
        )
        resources.extend(
            [
                Resource(f"{warehouse_id}_RECEIVING", "warehouse_receiving_bay", receiving, warehouse_id),
                Resource(f"{warehouse_id}_CROSSDOCK", "warehouse_crossdock_bay", crossdock, warehouse_id),
                Resource(f"{warehouse_id}_OUTBOUND", "warehouse_outbound_bay", outbound, warehouse_id),
            ]
        )

    vessel_calls: list[dict] = []
    containers: list[dict] = []
    warehouse_orders: list[dict] = []
    events: list[dict] = []
    operations: list[Operation] = []
    container_sequence = 1

    for ship_index in range(config.num_ships):
        vessel_id = f"VESSEL-{ship_index + 1:03d}"
        eta = config.start_time + timedelta(hours=ship_index * 14)
        berth_delay = rng.randint(30, 180) if rng.random() < config.disruption_rate else 0
        berth_start = eta + timedelta(minutes=berth_delay)
        berth_end = berth_start + timedelta(hours=8 + config.containers_per_ship / 20)
        vessel_calls.append(
            {
                "vessel_call_id": vessel_id,
                "vessel_name": f"MV Synthetic {ship_index + 1}",
                "voyage": f"V{config.seed % 100:02d}{ship_index + 1:02d}",
                "terminal_id": terminal_id,
                "eta": eta.isoformat(),
                "berth_start": berth_start.isoformat(),
                "berth_end": berth_end.isoformat(),
                "berth_delay_minutes": berth_delay,
                "container_count": config.containers_per_ship,
            }
        )
        events.append(
            {
                "timestamp": eta.isoformat(),
                "event_type": "vessel_eta",
                "entity_id": vessel_id,
                "source_system": "TOS",
                "value": eta.isoformat(),
            }
        )
        if berth_delay:
            events.append(
                {
                    "timestamp": (eta - timedelta(minutes=45)).isoformat(),
                    "event_type": "berth_delay",
                    "entity_id": vessel_id,
                    "source_system": "TOS",
                    "value": berth_delay,
                    "unit": "minutes",
                }
            )

        for container_index in range(config.containers_per_ship):
            container_id = _container_number(rng, container_sequence)
            container_sequence += 1
            warehouse = warehouses[rng.randrange(config.num_warehouses)]
            warehouse_id = warehouse["warehouse_id"]
            is_crossdock = rng.random() < config.crossdock_ratio
            commodity = rng.choice(
                ["patio_furniture", "bbq_units", "appliances", "retail_general", "auto_parts"]
            )
            size_teu = rng.choice([1, 1, 2])
            discharge_release = berth_start + timedelta(minutes=12 + container_index * 6)
            delivery_due = min(
                discharge_release + timedelta(hours=rng.randint(30, 60)),
                config.start_time + timedelta(days=config.horizon_days),
            )
            containers.append(
                {
                    "container_id": container_id,
                    "vessel_call_id": vessel_id,
                    "terminal_id": terminal_id,
                    "warehouse_id": warehouse_id,
                    "commodity": commodity,
                    "size_teu": size_teu,
                    "gross_weight_kg": rng.randint(8500, 28500),
                    "crossdock_required": is_crossdock,
                    "available_time": discharge_release.isoformat(),
                    "delivery_due": delivery_due.isoformat(),
                }
            )
            order_id = f"ORDER-{container_sequence - 1:07d}"
            warehouse_orders.append(
                {
                    "order_id": order_id,
                    "container_id": container_id,
                    "warehouse_id": warehouse_id,
                    "order_type": "crossdock" if is_crossdock else "storage",
                    "commodity": commodity,
                    "units": rng.randint(12, 48),
                    "customer_id": f"CUSTOMER-{rng.randint(1, 12):03d}",
                    "delivery_due": delivery_due.isoformat(),
                }
            )

            prefix = container_id
            discharge_id = f"{prefix}:DISCHARGE"
            gate_id = f"{prefix}:GATE_READY"
            dray_in_id = f"{prefix}:DRAY_IN"
            receive_id = f"{prefix}:RECEIVE"
            process_type = "CROSSDOCK" if is_crossdock else "STORAGE_PICK"
            process_id = f"{prefix}:{process_type}"
            outbound_id = f"{prefix}:OUTBOUND"
            dray_out_id = f"{prefix}:DRAY_OUT"
            delivery_id = f"{prefix}:DELIVERY"
            common = {"order_id": order_id, "vessel_call_id": vessel_id, "commodity": commodity}
            operations.extend(
                [
                    Operation(
                        discharge_id, container_id, "terminal_discharge", terminal_id,
                        "TERMINAL_CRANES", rng.randint(12, 24), discharge_release, delivery_due,
                        attributes=common,
                    ),
                    Operation(
                        gate_id, container_id, "terminal_gate_ready", terminal_id,
                        "TERMINAL_CRANES", rng.randint(6, 12), discharge_release, delivery_due,
                        dependencies=[discharge_id], attributes=common,
                    ),
                    Operation(
                        dray_in_id, container_id, "drayage_import", "NETWORK",
                        "DRAYAGE_TRUCKS", rng.randint(45, 95), discharge_release, delivery_due,
                        dependencies=[gate_id], attributes=common | {"destination": warehouse_id},
                    ),
                    Operation(
                        receive_id, container_id, "warehouse_receive", warehouse_id,
                        f"{warehouse_id}_RECEIVING", rng.randint(25, 55), discharge_release, delivery_due,
                        dependencies=[dray_in_id], attributes=common,
                    ),
                    Operation(
                        process_id, container_id,
                        "warehouse_crossdock" if is_crossdock else "warehouse_storage_pick",
                        warehouse_id, f"{warehouse_id}_CROSSDOCK",
                        rng.randint(45, 120) if is_crossdock else rng.randint(90, 240),
                        discharge_release, delivery_due, dependencies=[receive_id], attributes=common,
                    ),
                    Operation(
                        outbound_id, container_id, "warehouse_outbound", warehouse_id,
                        f"{warehouse_id}_OUTBOUND", rng.randint(25, 50), discharge_release, delivery_due,
                        dependencies=[process_id], attributes=common,
                    ),
                    Operation(
                        dray_out_id, container_id, "drayage_delivery", "NETWORK",
                        "DRAYAGE_TRUCKS", rng.randint(50, 110), discharge_release, delivery_due,
                        dependencies=[outbound_id], attributes=common,
                    ),
                    Operation(
                        delivery_id, container_id, "customer_delivery", "CUSTOMER-NETWORK",
                        "CUSTOMER_DOCKS", rng.randint(20, 45), discharge_release, delivery_due,
                        dependencies=[dray_out_id], attributes=common,
                    ),
                ]
            )

    return SyntheticDataset(
        vessel_calls=vessel_calls,
        containers=containers,
        warehouses=warehouses,
        warehouse_orders=warehouse_orders,
        events=sorted(events, key=lambda event: event["timestamp"]),
        resources=resources,
        operations=operations,
    )
