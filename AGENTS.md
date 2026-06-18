# Prototype Instructions

Run the local server yourself and open the preview in the in-app browser. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

## ADOPT design decisions

- Preserve the previous MeshPlan network-map composition: white utility header, deep navy side rail, metric strip, pale GIS map, right-hand inspector, and bottom time controls.
- ADOPT expands the map to four Vancouver-area terminals, BC Rail, four major warehouses, one Delta cross-dock, and customer clusters.
- The landing screen is interactive; future navigation destinations remain intentionally marked as coming soon.
- Source visual: `network-map-reference.png`.
- Map geometry uses the fixed Web Mercator bounds in `scripts/generate_basemap.py`; all network entities are stored as latitude/longitude and projected against those exact bounds in `src/App.jsx`.
