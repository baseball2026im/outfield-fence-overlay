#!/usr/bin/env python3
"""Convert data/field-overlay.kml → data/field-overlay.geojson.

Flattens the foldered KML into one FeatureCollection, carrying each Placemark's
folder, name, and description into GeoJSON properties so index.html can style by
folder without a KML runtime library. Points/LineStrings/Polygons supported.

Run:  python3 build-overlay-geojson.py
"""
import json
import os
import re
import xml.etree.ElementTree as ET

HERE = os.path.dirname(__file__)
KML = os.path.join(HERE, "data", "field-overlay.kml")
OUT = os.path.join(HERE, "data", "field-overlay.geojson")


def _strip_ns(tag):
    return tag.split("}", 1)[-1]


def _coords(text):
    pts = []
    for tok in text.replace("\n", " ").split():
        parts = tok.split(",")
        if len(parts) >= 2:
            pts.append([float(parts[0]), float(parts[1])])  # lon, lat
    return pts


def _text(el, name):
    child = el.find(f"./{{*}}{name}")
    return child.text.strip() if child is not None and child.text else ""


def parse():
    tree = ET.parse(KML)
    features = []

    def walk(el, folder):
        for child in el:
            tag = _strip_ns(child.tag)
            if tag == "Folder":
                fname = _text(child, "name") or folder
                walk(child, fname)
            elif tag == "Placemark":
                features.append(placemark(child, folder))

    def placemark(pm, folder):
        name = _text(pm, "name")
        desc = _text(pm, "description")
        geom = None
        for g in pm:
            gt = _strip_ns(g.tag)
            if gt == "Point":
                geom = {"type": "Point", "coordinates": _coords(_text(g, "coordinates"))[0]}
            elif gt == "LineString":
                geom = {"type": "LineString", "coordinates": _coords(_text(g, "coordinates"))}
            elif gt == "Polygon":
                ring = g.find(".//{*}coordinates")
                geom = {"type": "Polygon", "coordinates": [_coords(ring.text)]}
        return {
            "type": "Feature",
            "properties": {"folder": folder, "name": name, "description": desc},
            "geometry": geom,
        }

    root = tree.getroot()
    doc = root.find("./{*}Document")
    walk(doc if doc is not None else root, "")
    return {"type": "FeatureCollection", "features": [f for f in features if f["geometry"]]}


def main():
    fc = parse()
    with open(OUT, "w") as f:
        json.dump(fc, f, indent=2)
    folders = {}
    for feat in fc["features"]:
        folders[feat["properties"]["folder"]] = folders.get(feat["properties"]["folder"], 0) + 1
    print(f"Wrote {OUT}: {len(fc['features'])} features")
    for k, v in folders.items():
        print(f"  {k or '(root)'}: {v}")


if __name__ == "__main__":
    main()
