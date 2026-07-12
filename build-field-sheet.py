#!/usr/bin/env python3
"""Build field-sheet.html — a printable one-page field guide for placing the
removable outfield fence.

Renders the aerial image + fence overlay (Google satellite, so it aligns with the
surveyed coordinates like Google My Maps), generates three QR codes (interactive
Google My Maps view · KML download · Locus Map install), and writes a
self-contained A4 HTML page (image + QRs embedded as data URIs) with the purpose,
Locus import steps, and the walk-the-line procedure.

Run:  python3 build-field-sheet.py   (needs: segno, staticmap, Pillow)
"""
import base64
import io
import json
import os

import segno
from PIL import Image
from staticmap import CircleMarker, Line, StaticMap

HERE = os.path.dirname(__file__)
GEO = os.path.join(HERE, "data", "field-overlay.geojson")
APP_SHOT = os.path.join(HERE, "data", "locus-in-app.png")
OUT = os.path.join(HERE, "index.html")  # the guide is the site landing page
PDF = os.path.join(HERE, "field-sheet.pdf")

MYMAPS = "https://www.google.com/maps/d/viewer?mid=1lenM0C5zkyE6P6zIqa7H9a0x143gxus"
KML = "https://baseball2026im.github.io/outfield-fence-overlay/data/field-overlay.kml"
LOCUS = "https://www.locusmap.app/"
GOOGLE_SAT = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"

RED, WHITE, BLUE, YELLOW, BLACK, DARK = "#ff2d2d", "#ffffff", "#2b6cff", "#ffcc00", "#000000", "#5a4200"
ORANGE, CYAN = "#ff9500", "#00e5ff"  # bigger reference variants (read well on green)


def coords_of(feat):
    g = feat["geometry"]
    if g["type"] == "Point":
        return [g["coordinates"]]
    if g["type"] == "LineString":
        return g["coordinates"]
    if g["type"] == "Polygon":
        return g["coordinates"][0]
    return []


def render_aerial(fc):
    m = StaticMap(1000, 900, url_template=GOOGLE_SAT, tile_size=256)
    # lines first (arc on top of foul/backstop/PA), points last
    for f in fc["features"]:
        p, g = f["properties"], f["geometry"]
        n, fold = p["name"].lower(), p["folder"]
        if g["type"] == "LineString":
            pts = [(x, y) for x, y in g["coordinates"]]
            if fold == "Outfield arcs":
                if "operational" in n:
                    m.add_line(Line(pts, RED, 6))          # the fence line to build
                # reference arcs (90-122 m variants) are far larger than this
                # frame, so they're omitted here — the interactive map shows them.
            elif "backstop" in n:
                m.add_line(Line(pts, BLACK, 4))
            else:
                m.add_line(Line(pts, WHITE, 3))            # foul lines
        elif g["type"] == "Polygon":
            m.add_line(Line([(x, y) for x, y in g["coordinates"][0]], BLUE, 3))
    for f in fc["features"]:
        p, g = f["properties"], f["geometry"]
        if g["type"] != "Point":
            continue
        xy = tuple(g["coordinates"])
        fold = p["folder"]
        if fold == "Trial reference points":
            m.add_marker(CircleMarker(xy, YELLOW, 15)); m.add_marker(CircleMarker(xy, DARK, 8))
        elif fold == "Diamond":
            m.add_marker(CircleMarker(xy, WHITE, 13)); m.add_marker(CircleMarker(xy, BLUE, 7))
        else:  # chalk endpoints
            m.add_marker(CircleMarker(xy, WHITE, 12)); m.add_marker(CircleMarker(xy, RED, 6))

    # where the operational arc crosses the soccer penalty-area lines — the fixed,
    # painted ground references you can hit without a phone (white dot, black ring).
    for lon, lat in ((11.5297618, 48.0508600), (11.5298250, 48.0508156)):
        m.add_marker(CircleMarker((lon, lat), BLACK, 10))
        m.add_marker(CircleMarker((lon, lat), WHITE, 6))

    # center on the operational features only (reference arcs stay in fc but are
    # not drawn here; excluding them keeps the field from shrinking / clipping).
    op = [f for f in fc["features"]
          if not (f["properties"]["folder"] == "Outfield arcs"
                  and "reference" in f["properties"]["name"].lower())]
    xs = [c[0] for f in op for c in coords_of(f)]
    ys = [c[1] for f in op for c in coords_of(f)]
    center = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2]
    img = m.render(center=center, zoom=20)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def qr(url):
    return segno.make(url, error="m").svg_data_uri(scale=4, border=2, dark="#111")


def embed_shot(path, width=480, quality=82, crop=(0, 180, 1179, 1720)):
    im = Image.open(path).convert("RGB")
    if crop and crop[2] <= im.width and crop[3] <= im.height:
        im = im.crop(crop)  # trim the status bar / extreme portrait to a ~0.68 aspect
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    fc = json.load(open(GEO))
    aerial = render_aerial(fc)
    html = TEMPLATE.format(
        aerial=aerial,
        shot=embed_shot(APP_SHOT),
        qr_mymaps=qr(MYMAPS),
        qr_kml=qr(KML),
        qr_locus=qr(LOCUS),
    )
    with open(OUT, "w") as f:
        f.write(html)
    print(f"Wrote {OUT} ({len(html)//1024} KB)")

    import weasyprint  # noqa: PLC0415 — heavy import, only when building
    doc = weasyprint.HTML(string=html).render()
    doc.write_pdf(PDF)
    print(f"Wrote {PDF} ({len(doc.pages)} page{'s' if len(doc.pages) != 1 else ''})")


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Outfield Fence — Field Sheet · Grünwald Baseballfeld</title>
<style>
  :root {{ --ink:#14181d; --mut:#5b6672; --line:#d7dde5; --red:#d92d2d; }}
  * {{ box-sizing: border-box; }}
  html,body {{ margin:0; color:var(--ink);
    font-family: system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
  .page {{ width:210mm; min-height:297mm; margin:0 auto; padding:11mm 12mm; }}
  h1 {{ font-size:20px; margin:0; }}
  .sub {{ color:var(--mut); font-size:12px; margin:2px 0 7px; }}
  .purpose {{ font-size:12px; line-height:1.42; margin:0 0 9px; }}
  .aerial {{ max-height:72mm; width:auto; max-width:100%; margin:2px auto 4px; display:block; border-radius:6px; border:1px solid var(--line); }}
  .cap {{ font-size:9.5px; color:var(--mut); margin:0 0 9px; text-align:center; line-height:1.3; }}
  .qrs {{ display:flex; gap:10px; margin:0 0 11px; }}
  .qr {{ flex:1; border:1px solid var(--line); border-radius:6px; padding:7px 6px; text-align:center; }}
  .qr img {{ width:74px; height:74px; }}
  .qr .t {{ font-size:12px; font-weight:600; margin-top:3px; }}
  .qr .d {{ font-size:9.5px; color:var(--mut); line-height:1.3; margin-top:1px; }}
  .cols {{ display:flex; gap:10px; align-items:flex-start; }}
  .col {{ flex:1; }}
  .shot {{ flex:0 0 46mm; display:flex; flex-direction:column; align-items:center; }}
  .shot img {{ width:44mm; height:auto; border-radius:9px; border:1px solid var(--line); }}
  .scap {{ width:44mm; font-size:9.5px; color:var(--mut); line-height:1.3; margin-top:4px; text-align:center; }}
  h2 {{ font-size:13px; margin:2px 0 5px; padding-bottom:3px; border-bottom:2px solid var(--red); }}
  ol {{ margin:0; padding-left:17px; }}
  ol li {{ font-size:11.5px; line-height:1.42; margin-bottom:4px; }}
  .foot {{ margin-top:11px; padding-top:7px; border-top:1px solid var(--line);
    font-size:10px; color:var(--mut); line-height:1.45; }}
  .foot b {{ color:var(--ink); }}
  @media print {{
    @page {{ size:A4 portrait; margin:0; }}
    .page {{ margin:0; }}
    a {{ color:inherit; text-decoration:none; }}
  }}
</style>
</head>
<body>
<div class="page">
  <h1>Removable Outfield Fence — Field Sheet</h1>
  <div class="sub">Grünwald Baseballfeld · small-variant arc (80 m to centre)</div>

  <p class="purpose">
    This dual-use turf field has <b>no permanent markings</b>, so the outfield fence is re-placed
    from scratch each session. The <b>red curve</b> is the <b>operational</b> fence line; you can
    build a <b>bigger variant</b> instead <b>where the trees and side-banks allow</b> (the
    interactive map shows all options). The diamond and foul lines orient you, and the five yellow
    pins are quick
    anchors. With your phone's GPS and this overlay, you just walk the line and stand the
    fence in the same spot every time.
  </p>

  <img class="aerial" src="{aerial}" alt="Aerial view of the field with the fence overlay" />
  <div class="cap">Red = operational fence line · yellow = the 5 pins · white = diamond &amp; foul lines · black = backstop · blue box = soccer penalty area, where the two arc crossings (white/black marks) are fixed ground references.</div>

  <div class="qrs">
    <div class="qr">
      <img src="{qr_mymaps}" alt="Google My Maps QR" />
      <div class="t">Interactive map</div>
      <div class="d">View the overlay in Google&nbsp;My&nbsp;Maps.</div>
    </div>
    <div class="qr">
      <img src="{qr_kml}" alt="KML download QR" />
      <div class="t">Fence file (KML)</div>
      <div class="d">Open in Locus Map — import from URL or "open with".</div>
    </div>
    <div class="qr">
      <img src="{qr_locus}" alt="Locus Map install QR" />
      <div class="t">Install the app</div>
      <div class="d"><b>Locus Map Lite</b> (iPhone) · <b>Locus Map</b> (Android) — free, live GPS.</div>
    </div>
  </div>

  <div class="cols">
    <div class="col">
      <h2>Load the fence file into Locus Map</h2>
      <ol>
        <li>Install the app (bottom QR): iPhone <b>Locus Map Lite</b>, Android <b>Locus Map</b>.</li>
        <li><b>iPhone / any phone:</b> in Locus Map &rarr; menu (&#9776;) &rarr; <b>Import</b> &rarr; <b>from URL</b>, and paste the <b>Fence file</b> link (scan its QR to copy it).</li>
        <li><b>Android shortcut:</b> just scan the <b>Fence file</b> QR &rarr; the file downloads &rarr; tap <b>Open with Locus Map</b>.</li>
        <li>Import into a folder (e.g.&nbsp;"Baseball"). The arc, diamond and pins now show on the map.</li>
      </ol>
    </div>
    <div class="col">
      <h2>Walk the line &amp; place the fence</h2>
      <ol>
        <li>Tap the <b>GPS / centre</b> button so your dot shows and follows you; wait a moment for the fix to settle.</li>
        <li><b>Check:</b> stand where the arc crosses the soccer penalty-area lines — a fixed painted reference (or a foul corner) — and confirm your dot sits there.</li>
        <li><b>Roll out roughly:</b> use the aerial above to get oriented, then lay the fence out loosely in the arc's shape between the two foul corners.</li>
        <li><b>Fine-position with the phone:</b> walk the line and nudge each section until your dot sits on the <b>arc line</b>, then stand it upright. The 5 pins mark the key points (corners, mid-arc, centre).</li>
        <li><b>Verify:</b> tape-measure home&nbsp;&rarr;&nbsp;centre pin &asymp; 80&nbsp;m; nudge as needed.</li>
      </ol>
    </div>
    <div class="shot">
      <img src="{shot}" alt="Locus Map showing live position on the overlay" />
      <div class="scap">In Locus Map: your <b>blue dot</b> on the overlay lines. Keep it on the arc as you walk; the scale bar (top-left) shows metres.</div>
    </div>
  </div>

  <div class="foot">
    <b>Arc:</b> apex 80&nbsp;m on bearing 193.5&deg; (home&rarr;2B) · radius 46.6&nbsp;m · length ~115.5&nbsp;m · 39 panels @&nbsp;3&nbsp;m &nbsp;·&nbsp;
    <b>Home plate:</b> 48.051415,&nbsp;11.530371 &nbsp;·&nbsp;
    <b>Precision:</b> a modern phone's GPS is easily good enough for a training fence; for extra precision, anchor the 5 pins by tape from home plate.
  </div>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    main()
