# Outfield Fence Overlay — Grünwald Baseballfeld

Map data + a lightweight web viewer for setting up the **removable outfield
fence** on a dual-use turf field (baseball / soccer) in Grünwald. Every session
starts from bare turf with no permanent ground markers, so this repo carries the
surveyed geometry and the operational fence arc as portable GIS files you can
load on a phone and **walk the line** with a live GPS dot.

## The operational arc

A single **small-variant** arc (fits the rules-compliant senior/U15 arcs run
into the tree line and the soccer pitch, so those are kept as reference-only):

- **Scale:** BBSV U12 Schüler (60-ft / Little-League).
- **Geometry:** apex distance **D = 80 m** on bearing 193.46° (home → 2nd base);
  radius **R = 46.56 m**, arc length **≈ 115.5 m**, **39 segments** at 3.0 m
  (10-ft chain-link panels). Foul corners pinned to the surveyed chalk endpoints.

## Viewer

`index.html` is a self-contained [Leaflet](https://leafletjs.com/) page on an
Esri satellite basemap. It renders the full overlay (operational arc in **red**,
reference arcs dashed, diamond, foul lines, backstop, soccer penalty area, and
the 5 trial pins) and has a **⌖ locate** button that shows your live GPS
position + accuracy circle — open it on your phone at the field and walk the red
line to place the fence.

**Enable GitHub Pages** (Settings → Pages → Deploy from branch → `main` / root),
then open the published URL on your phone. Geolocation requires HTTPS, which
GitHub Pages provides.

## Data files (`data/`)

| File | What |
| --- | --- |
| `gruenwald-baseballfeld.geojson` | The operational arc only (39-pt LineString). |
| `gruenwald-baseballfeld.kml` | Same arc in KML (for Google My Maps / AR apps). |
| `field-overlay.kml` / `.gpx` | **Full** foldered overlay: arcs + references + diamond + foul lines + backstop + soccer PA + trial pins. Best single import for Google My Maps / uMap / Locus. |
| `field-trial-points.kml` / `.gpx` | Just the 5 named pins (RF corner, RF mid-arc, CF apex, LF mid-arc, LF corner) for tape-measure verification. |
| `field-overlay.geojson` | Flattened overlay the viewer loads (generated from the KML). |
| `gruenwald-baseballfeld-geometry.yaml` | Source of truth: every surveyed waypoint + the design parameters. |
| `small-variant-arc.png` | Rendered reference plot of the arc. |

## Regenerating

`field-overlay.geojson` is derived from `field-overlay.kml`:

```bash
python3 build-overlay-geojson.py
```

The KML/GeoJSON/GPX artifacts themselves are emitted from the surveyed geometry
by the `emit-arc-artifacts.py` generator in the source spec (kept private); this
repo is the published data + viewer split of that work.

## Coordinates

Home plate: `48.05141513, 11.53037099` (Grünwald). Diamond symmetry axis
(home → 2B) 193.46°. All bearings/distances are in
`gruenwald-baseballfeld-geometry.yaml`.

## Status

The original goal was a **ground-anchored AR overlay**, but no free-tier iOS app
delivered outfield-precision AR — so this **2D real-time GPS "follow the line"**
viewer is the operational method. Re-evaluate AR when a viable free app appears.
