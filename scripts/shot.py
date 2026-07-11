"""Render 300-mile radius circles on mapdevelopers.com's Draw Circle Tool.

Framing: the circle touches the top and bottom edges of the frame and the
left/right padding is 0.75 * radius, giving a 3.5r x 2r (1.75:1) frame.
The frame is held at a fixed 3454x1976 px so every pic in the set matches;
zoom is solved per city, since Mercator's scale varies with latitude.
"""
from playwright.sync_api import sync_playwright
import urllib.parse, json, math, sys, os

RADIUS_M = round(300 * 1609.344)
WIDTH, HEIGHT = 1727, 988          # CSS px; 2x device scale -> 3454x1976
R_EARTH = 6371008.8
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else "."

# Largest city of each territory (with the airport that serves it).
CITIES = [
    # city,             state/territory,            lat,      lng      # airport
    ("Washington",      "District_of_Columbia",    38.9072,  -77.0369),  # DCA/IAD
    ("Dededo",          "Guam",                    13.5187,  144.8385),  # GUM
    ("Charlotte_Amalie","US_Virgin_Islands",       18.3419,  -64.9307),  # STT
    ("San_Juan",        "Puerto_Rico",             18.4655,  -66.1057),  # SJU
]

mercY = lambda p: 128 * (1 - math.log(math.tan(math.pi / 4 + p / 2)) / math.pi)

def frame_for(lat):
    """Zoom + centre latitude that make the circle span the full frame height."""
    d = RADIUS_M / R_EARTH
    p0 = math.radians(lat)
    yN, yS = mercY(p0 + d), mercY(p0 - d)
    zoom = math.log2(HEIGHT / (yS - yN))
    # Mercator stretches the circle's northern half, so its bbox midpoint sits
    # north of the circle's centre point -- centre the frame on the bbox.
    yc = (yN + yS) / 2
    clat = math.degrees(2 * math.atan(math.exp(math.pi * (1 - yc / 128))) - math.pi / 2)
    return zoom, clat

APPLY = """({lat, lng, zoom}) => {
  const m = window.map && window.map.setCenter ? window.map
          : Object.values(window).find(v => v && v.setCenter && v.setZoom);
  if (!m) return false;
  Object.assign(document.body.style, {margin: '0', overflow: 'hidden'});
  for (const id of ['map_canvas', 'map_area']) Object.assign(document.getElementById(id).style,
    {position: 'fixed', top: '0', left: '0', width: '100vw', height: '100vh', zIndex: '99999', margin: '0'});
  google.maps.event.trigger(m, 'resize');
  m.setOptions({isFractionalZoomEnabled: true, disableDefaultUI: true, mapTypeControl: false,
                fullscreenControl: false, streetViewControl: false, zoomControl: false});
  m.setCenter({lat, lng});
  m.setZoom(zoom);
  const css = document.createElement('style');
  css.textContent = `.gmnoprint,.gm-style-cc,.gm-fullscreen-control,
    a[href*="maps.google"],img[alt="Google"],.gm-svpc{display:none!important}`;
  document.head.appendChild(css);
  return true;
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    for city, terr, lat, lng in CITIES:
        zoom, clat = frame_for(lat)
        circles = [[RADIUS_M, lat, lng, "#000000", "#AAAAAA", 0.4]]
        url = ("https://www.mapdevelopers.com/draw-circle-tool.php?circles="
               + urllib.parse.quote(json.dumps(circles)))
        pg = b.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=2)
        pg.goto(url, wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(3000)
        if not pg.evaluate(APPLY, {"lat": clat, "lng": lng, "zoom": zoom}):
            sys.exit(f"could not reach map object for {city}")
        pg.wait_for_timeout(7000)   # let tiles settle
        out = os.path.join(OUTDIR, f"short-haul_{terr}_{city}.png")
        pg.locator("#map_canvas").screenshot(path=out)
        pg.close()
        print(f"{terr}/{city}: zoom={zoom:.4f} centre=({clat:.4f},{lng}) -> {out}")
    b.close()
