#!/usr/bin/env python3
"""Build the fixed ADOPT basemap from OpenStreetMap raster tiles."""

from __future__ import annotations

import io
import math
import urllib.request
from pathlib import Path

from PIL import Image


ZOOM = 11
BOUNDS = {"west": -123.35, "east": -122.45, "north": 49.40, "south": 48.98}
OUTPUT = Path(__file__).resolve().parents[1] / "public" / "assets" / "lower-mainland-map.png"


def world_pixel(lat: float, lon: float) -> tuple[float, float]:
    scale = 256 * (2 ** ZOOM)
    x = (lon + 180.0) / 360.0 * scale
    lat_rad = math.radians(lat)
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * scale
    return x, y


def main() -> None:
    left, top = world_pixel(BOUNDS["north"], BOUNDS["west"])
    right, bottom = world_pixel(BOUNDS["south"], BOUNDS["east"])
    min_x, max_x = math.floor(left / 256), math.floor(right / 256)
    min_y, max_y = math.floor(top / 256), math.floor(bottom / 256)
    canvas = Image.new("RGB", ((max_x - min_x + 1) * 256, (max_y - min_y + 1) * 256))
    headers = {"User-Agent": "ADOPT-prototype/1.0 (local product prototype)"}
    for tile_y in range(min_y, max_y + 1):
        for tile_x in range(min_x, max_x + 1):
            url = f"https://tile.openstreetmap.org/{ZOOM}/{tile_x}/{tile_y}.png"
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as response:
                tile = Image.open(io.BytesIO(response.read())).convert("RGB")
            canvas.paste(tile, ((tile_x - min_x) * 256, (tile_y - min_y) * 256))
    crop = (
        round(left - min_x * 256), round(top - min_y * 256),
        round(right - min_x * 256), round(bottom - min_y * 256),
    )
    cropped = canvas.crop(crop).resize((1800, 1125), Image.Resampling.LANCZOS)
    cropped.save(OUTPUT, optimize=True)
    print(f"Wrote {OUTPUT} ({cropped.width}x{cropped.height})")


if __name__ == "__main__":
    main()
