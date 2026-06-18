# ADOPT

**Advanced Drayage Optimizer** is an interactive prototype for visualizing and planning drayage operations across the Vancouver Lower Mainland.

The current landing page provides a georeferenced network map connecting:

- Deltaport, Vanterm, Centerm, and Fraser Surrey Docks
- BC Rail North Vancouver Yard
- YVR, Langley, North Vancouver, and Vancouver warehouses
- Delta Cross-dock
- Regional Costco, Walmart, Home Depot, and Real Canadian Superstore customer clusters

## Prototype

```bash
pnpm install
pnpm dev
```

Open `http://127.0.0.1:5173`.

## Annual scenario data

The bundled `drayage-gen-data` utility creates a deterministic 365-day scenario containing 3,650 vessel calls, 73,000 containers, 50 products, and facility capacity data.

```bash
python3 drayage-gen-data/generate_adopt_year.py
```

Generated datasets are written to `public/data/`. The fixed Web Mercator basemap can be rebuilt from OpenStreetMap tiles with:

```bash
python3 scripts/generate_basemap.py
```

Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

## Validation

```bash
pnpm build
cd drayage-gen-data
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
