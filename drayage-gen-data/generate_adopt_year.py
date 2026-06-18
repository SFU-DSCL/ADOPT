#!/usr/bin/env python3
"""Generate a deterministic year of Vancouver-area ADOPT operating data."""

from __future__ import annotations

import csv
import json
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "data"
START = date(2026, 7, 1)
SEED = 20260618

PORTS = [
    ("PORT-DELTAPORT", "Deltaport", "Delta", 10, 49.023293, -123.157167),
    ("PORT-VANTERM", "Vanterm", "Vancouver", 10, 49.2895, -123.0405),
    ("PORT-CENTERM", "Centerm", "Vancouver", 10, 49.2915, -123.0720),
    ("PORT-FSD", "Fraser Surrey Docks", "Surrey", 10, 49.1950, -122.9220),
]

WAREHOUSES = [
    ("WH-YVR", "YVR Logistics Centre", "YVR", "warehouse", 20, 49.1940, -123.1780),
    ("WH-LANGLEY", "Langley Distribution Campus", "Langley", "warehouse", 20, 49.1040, -122.6600),
    ("WH-NORTH-VAN", "North Vancouver DC", "North Vancouver", "warehouse", 20, 49.3120, -123.0440),
    ("WH-VANCOUVER", "Vancouver Fulfilment Hub", "Vancouver", "warehouse", 20, 49.2280, -123.0790),
    ("WH-DELTA-XD", "Delta Cross-dock", "Delta", "crossdock", 20, 49.1080, -123.0260),
]

RAIL = ("RAIL-BC", "BC Rail North Vancouver Yard", "North Vancouver", 49.3090, -123.0320)

CITIES = ["YVR", "Langley", "North Vancouver", "Vancouver", "Delta"]
BRANDS = ["Costco", "Walmart", "Home Depot", "Real Canadian Superstore"]
CUSTOMER_POINTS = {
    "YVR": [(49.178, -123.130), (49.166, -123.135), (49.181, -123.093), (49.176, -123.126)],
    "Langley": [(49.116, -122.678), (49.105, -122.666), (49.112, -122.672), (49.104, -122.654)],
    "North Vancouver": [(49.321, -123.073), (49.312, -123.082), (49.312, -123.042), (49.320, -123.095)],
    "Vancouver": [(49.277, -123.114), (49.258, -123.032), (49.265, -123.070), (49.257, -123.116)],
    "Delta": [(49.154, -122.950), (49.118, -122.890), (49.151, -122.908), (49.132, -122.892)],
}

PRODUCTS = [
    ("P001", "Flat-pack patio furniture", "home_outdoor"),
    ("P002", "Gas barbecue grills", "home_outdoor"),
    ("P003", "Cordless power tools", "hardware"),
    ("P004", "LED television sets", "electronics"),
    ("P005", "Refrigerators", "appliances"),
    ("P006", "Washing machines", "appliances"),
    ("P007", "Microwave ovens", "appliances"),
    ("P008", "Ceramic floor tile", "building_materials"),
    ("P009", "Laminate flooring", "building_materials"),
    ("P010", "Kitchen cabinets", "building_materials"),
    ("P011", "Bathroom vanities", "building_materials"),
    ("P012", "Solar panels", "energy"),
    ("P013", "Electric bicycles", "mobility"),
    ("P014", "Passenger vehicle tires", "automotive"),
    ("P015", "Automotive batteries", "automotive"),
    ("P016", "Motor oil cases", "automotive"),
    ("P017", "Canned tomatoes", "grocery"),
    ("P018", "Pasta and noodles", "grocery"),
    ("P019", "Roasted coffee beans", "grocery"),
    ("P020", "Bottled sparkling water", "beverages"),
    ("P021", "Olive oil", "grocery"),
    ("P022", "Rice sacks", "grocery"),
    ("P023", "Frozen seafood", "cold_chain"),
    ("P024", "Frozen vegetables", "cold_chain"),
    ("P025", "Fresh citrus fruit", "produce"),
    ("P026", "Bananas", "produce"),
    ("P027", "Packaged snack foods", "grocery"),
    ("P028", "Paper towels", "household"),
    ("P029", "Laundry detergent", "household"),
    ("P030", "Dishwasher tablets", "household"),
    ("P031", "Pet food", "pet_care"),
    ("P032", "Diapers", "personal_care"),
    ("P033", "Shampoo and conditioner", "personal_care"),
    ("P034", "Office chairs", "furniture"),
    ("P035", "Mattresses", "furniture"),
    ("P036", "Modular shelving", "furniture"),
    ("P037", "Lawn mowers", "home_outdoor"),
    ("P038", "Garden soil bags", "home_outdoor"),
    ("P039", "Seasonal decorations", "retail_general"),
    ("P040", "Cotton apparel", "apparel"),
    ("P041", "Athletic footwear", "apparel"),
    ("P042", "School backpacks", "apparel"),
    ("P043", "Laptop computers", "electronics"),
    ("P044", "Computer monitors", "electronics"),
    ("P045", "Mobile phone accessories", "electronics"),
    ("P046", "LED light fixtures", "hardware"),
    ("P047", "Plumbing fixtures", "hardware"),
    ("P048", "Insulation rolls", "building_materials"),
    ("P049", "Commercial cleaning supplies", "household"),
    ("P050", "Reusable storage bins", "household"),
]


def write_csv(path: Path, fields: list[str], rows) -> int:
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def customers() -> list[dict]:
    rows = []
    sequence = 1
    for city in CITIES:
        for brand, (lat, lon) in zip(BRANDS, CUSTOMER_POINTS[city]):
            rows.append({
                "customer_id": f"CUST-{sequence:03d}", "name": brand, "city": city,
                "display_name": f"{brand} · {city}", "lat": lat, "lon": lon,
            })
            sequence += 1
    return rows


def generate() -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    customer_rows = customers()
    location_rows = []
    for item in PORTS:
        location_rows.append(dict(zip(
            ["location_id", "name", "city", "capacity", "lat", "lon"], item
        )) | {"type": "port", "capacity_unit": "gates"})
    for location_id, name, city, kind, bays, lat, lon in WAREHOUSES:
        location_rows.append({
            "location_id": location_id, "name": name, "city": city, "type": kind,
            "capacity": bays, "capacity_unit": "bays", "lat": lat, "lon": lon,
        })
    location_rows.append({
        "location_id": RAIL[0], "name": RAIL[1], "city": RAIL[2], "type": "rail",
        "capacity": 12, "capacity_unit": "tracks", "lat": RAIL[3], "lon": RAIL[4],
    })

    write_csv(OUTPUT / "locations.csv", list(location_rows[0]), location_rows)
    write_csv(OUTPUT / "customers.csv", list(customer_rows[0]), customer_rows)
    write_csv(OUTPUT / "products.csv", ["product_id", "product_name", "category"], (
        {"product_id": p[0], "product_name": p[1], "category": p[2]} for p in PRODUCTS
    ))

    vessel_fields = ["vessel_call_id", "service_date", "vessel_name", "terminal_id", "eta", "gate_count", "container_count"]
    container_fields = ["container_id", "vessel_call_id", "service_date", "terminal_id", "product_id", "product_name", "warehouse_id", "customer_id", "rail_transfer", "size_teu", "status", "planned_gate_time", "delivery_due"]
    daily_fields = ["service_date", "vessel_calls", "containers", "rail_transfers", "crossdock_moves", "late_moves"]
    vessel_path = OUTPUT / "vessel_calls.csv"
    container_path = OUTPUT / "containers.csv"
    daily_rows = []
    total_containers = 0

    with vessel_path.open("w", newline="", encoding="utf-8") as vessel_file, container_path.open("w", newline="", encoding="utf-8") as container_file:
        vessel_writer = csv.DictWriter(vessel_file, fieldnames=vessel_fields)
        container_writer = csv.DictWriter(container_file, fieldnames=container_fields)
        vessel_writer.writeheader()
        container_writer.writeheader()
        container_sequence = 1
        vessel_sequence = 1
        for day_index in range(365):
            service_day = START + timedelta(days=day_index)
            day_containers = rail_count = crossdock_count = late_count = 0
            for call_index in range(10):
                terminal = PORTS[(day_index + call_index) % len(PORTS)]
                eta = datetime.combine(service_day, time(0, 30)) + timedelta(minutes=call_index * 138)
                container_count = 20
                vessel_id = f"VC-{vessel_sequence:06d}"
                vessel_writer.writerow({
                    "vessel_call_id": vessel_id, "service_date": service_day.isoformat(),
                    "vessel_name": f"MV Pacific {vessel_sequence:04d}", "terminal_id": terminal[0],
                    "eta": eta.isoformat(), "gate_count": 10, "container_count": container_count,
                })
                vessel_sequence += 1
                for offset in range(container_count):
                    product = PRODUCTS[rng.randrange(len(PRODUCTS))]
                    warehouse = WAREHOUSES[rng.randrange(len(WAREHOUSES))]
                    customer = customer_rows[rng.randrange(len(customer_rows))]
                    rail = rng.random() < 0.14
                    late = rng.random() < 0.038
                    status = "late" if late else rng.choice(["planned", "at_port", "in_transit", "delivered"])
                    gate_time = eta + timedelta(minutes=90 + offset * 14)
                    container_writer.writerow({
                        "container_id": f"ADPU{container_sequence:07d}", "vessel_call_id": vessel_id,
                        "service_date": service_day.isoformat(), "terminal_id": terminal[0],
                        "product_id": product[0], "product_name": product[1], "warehouse_id": warehouse[0],
                        "customer_id": customer["customer_id"], "rail_transfer": str(rail).lower(),
                        "size_teu": rng.choice([1, 1, 2]), "status": status,
                        "planned_gate_time": gate_time.isoformat(),
                        "delivery_due": (gate_time + timedelta(hours=rng.randint(8, 44))).isoformat(),
                    })
                    container_sequence += 1
                    day_containers += 1
                    rail_count += int(rail)
                    crossdock_count += int(warehouse[0] == "WH-DELTA-XD")
                    late_count += int(late)
            total_containers += day_containers
            daily_rows.append({
                "service_date": service_day.isoformat(), "vessel_calls": 10,
                "containers": day_containers, "rail_transfers": rail_count,
                "crossdock_moves": crossdock_count, "late_moves": late_count,
            })

    write_csv(OUTPUT / "daily_summary.csv", daily_fields, daily_rows)
    sample_routes = []
    for index in range(14):
        port = PORTS[index % len(PORTS)]
        warehouse = WAREHOUSES[(index * 2) % len(WAREHOUSES)]
        customer = customer_rows[(index * 3) % len(customer_rows)]
        product = PRODUCTS[(index * 7) % len(PRODUCTS)]
        sample_routes.append({
            "id": f"ADPU{index + 1:07d}", "product": product[1], "port": port[0],
            "warehouse": warehouse[0], "customer": customer["customer_id"],
            "status": ["planned", "in_transit", "delivered", "late"][index % 4],
            "progress": round(0.08 + (index % 8) * 0.11, 2),
        })

    manifest = {
        "name": "ADOPT Vancouver annual scenario", "generated_at": datetime.now().isoformat(timespec="seconds"),
        "start_date": START.isoformat(), "end_date": (START + timedelta(days=364)).isoformat(),
        "seed": SEED, "vessel_calls": 3650, "ships_per_day": 10, "containers": total_containers,
        "ports": len(PORTS), "port_gates_each": 10, "warehouses": len(WAREHOUSES),
        "warehouse_bays_each": 20, "customers": len(customer_rows), "products": len(PRODUCTS),
        "locations": location_rows, "customers_detail": customer_rows, "sample_routes": sample_routes,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = generate()
    print(json.dumps(result | {"locations": "see manifest.json", "customers_detail": "see customers.csv", "sample_routes": "see manifest.json"}, indent=2))
