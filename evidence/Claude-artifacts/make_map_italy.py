#!/usr/bin/env python3
"""
make_map_italy.py -- optimized SEBD route over a real map of Italy, with
city/venue-name labels, repeat venues collapsed + marked, and sea-crossing legs
drawn dashed (detected geometrically against the land polygons, not hardcoded).

Outputs: sebd_route_italy.png, sebd_route_italy.svg
"""
import re, json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.lines import Line2D
import trip                                         # CITIES, name

SEA, LAND, BORDER, ROUTE, REPEAT = "#dce8f5", "#f2efe6", "#9aa0a6", "#c0392b", "#d35400"
CENTER_LON = 12.6          # west/east label-side split

# --- Italy polygons ----------------------------------------------------------
def exteriors(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "Polygon":
        yield c[0]
    elif t == "MultiPolygon":
        for poly in c:
            yield poly[0]

gj = json.load(open("italy-regions.geojson"))

def ring_area(ring):                                # |shoelace|, deg^2 (relative)
    x = np.asarray([p[0] for p in ring]); y = np.asarray([p[1] for p in ring])
    return abs(np.dot(x[:-1], y[1:]) - np.dot(x[1:], y[:-1])) / 2.0

# one record per connected land polygon (region name, Path, area, vertices)
land_rings, rings = [], []
for feat in gj["features"]:
    reg = feat["properties"].get("reg_name", "?")
    for ring in exteriors(feat["geometry"]):
        land_rings.append(ring)
        rings.append((reg, Path(np.asarray(ring)), ring_area(ring), np.asarray(ring)))

def containing_ring(lo, la):
    pt = [(lo, la)]
    cands = [(a, i, reg) for i, (reg, P, a, _) in enumerate(rings)
             if P.contains_points(pt)[0]]
    if cands:
        return min(cands)                           # smallest containing ring = island
    best = None                                     # fallback: nearest ring by vertex
    for i, (reg, P, a, v) in enumerate(rings):
        d = ((v[:, 0] - lo) ** 2 + (v[:, 1] - la) ** 2).min()
        if best is None or d < best[0]:
            best = (d, a, i, reg)
    return (best[1], best[2], best[3])

def landmass(lo, la):
    """Group a point by landmass: a named big island, a small island, or mainland."""
    area, idx, reg = containing_ring(lo, la)
    if reg in ("Sicilia", "Sardegna"):
        return reg                                  # the two big islands, by region
    if area < 0.5:
        return ("isle", idx)                        # small island polygon (Elba, Ischia)
    return "mainland"

# --- route + venues ----------------------------------------------------------
pos2no = {}
for line in open("route_optimized.pl"):
    m = re.match(r"\s*visit\(\s*(\d+),\s*(\d+)\)", line)
    if m:
        pos2no[int(m.group(1))] = int(m.group(2))
order = [pos2no[p] for p in sorted(pos2no)]
info  = {no: (city, yr, la, lo) for (no, yr, city, la, lo) in trip.CITIES}
lat   = {no: info[no][2] for no in info}
lon   = {no: info[no][3] for no in info}

# collapse editions that share a location (same lat,lon)
locs = {}                                           # (lat,lon) -> dict
for no in order:
    city, yr, la, lo = info[no]
    locs.setdefault((la, lo), {"city": city, "lon": lo, "lat": la, "eds": []})
    locs[(la, lo)]["eds"].append((no, yr))

# --- figure ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.6, 9.6))
ax.set_facecolor(SEA)
for ring in land_rings:
    xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
    ax.fill(xs, ys, facecolor=LAND, edgecolor=BORDER, linewidth=0.4, zorder=1)

# landmass per venue; a leg is a sea crossing iff it joins two different landmasses
lm = {no: landmass(lon[no], lat[no]) for no in order}
island_venues = [(info[no][0], lm[no]) for no in dict.fromkeys(order) if lm[no] != "mainland"]

sea_legs = []
for a, b in zip(order, order[1:]):
    if (lat[a], lon[a]) == (lat[b], lon[b]):
        continue                                    # zero-length twin hop
    dashed = lm[a] != lm[b]
    if dashed:
        sea_legs.append((info[a][0], info[b][0]))
    ax.plot([lon[a], lon[b]], [lat[a], lat[b]], color=ROUTE, lw=1.6,
            alpha=0.9, zorder=3, linestyle=(0, (4, 3)) if dashed else "-")

# markers
for (la, lo), d in locs.items():
    nums = [n for n, _ in d["eds"]]
    if 1 in nums:
        ax.scatter([lo], [la], s=170, marker="*", color="green",
                   edgecolor="k", linewidth=0.4, zorder=6)
    elif 34 in nums:
        ax.scatter([lo], [la], s=120, marker="s", color="crimson",
                   edgecolor="k", linewidth=0.4, zorder=6)
    elif len(d["eds"]) > 1:                          # repeat venue
        ax.scatter([lo], [la], s=85, marker="D", facecolor="white",
                   edgecolor=REPEAT, linewidth=1.6, zorder=6)
        ax.scatter([lo], [la], s=8, marker="D", color=REPEAT, zorder=7)
    else:
        ax.scatter([lo], [la], s=20, color="#222", zorder=5)

# --- labels with leader lines + vertical de-collision ------------------------
def label_for(d):
    eds = sorted(d["eds"], key=lambda e: e[1])
    yrs = "·".join("’%02d" % (y % 100) for _, y in eds)
    if 1 in [n for n, _ in eds]:
        return "Gizzeria Lido\n(start ’93)"
    if 34 in [n for n, _ in eds]:
        return "Senigallia\n(end ’26)"
    if len(eds) > 1:
        return "%s ×%d (%s)" % (d["city"], len(eds), yrs)
    return d["city"]

MINSEP = 0.34
for side in ("L", "R"):
    col = [d for d in locs.values() if (d["lon"] < CENTER_LON) == (side == "L")]
    col.sort(key=lambda d: d["lat"])
    cur = -99.0
    for d in col:
        ly = max(d["lat"], cur + MINSEP)
        cur = ly
        lx = d["lon"] + (-0.55 if side == "L" else 0.55)
        ha = "right" if side == "L" else "left"
        bold = len(d["eds"]) > 1 or 1 in [n for n, _ in d["eds"]] or 34 in [n for n, _ in d["eds"]]
        ax.annotate(label_for(d), (d["lon"], d["lat"]), xytext=(lx, ly),
                    textcoords="data", ha=ha, va="center", fontsize=6.6,
                    fontweight="bold" if bold else "normal",
                    color="#111",
                    arrowprops=dict(arrowstyle="-", lw=0.4, color="#888",
                                    shrinkA=0, shrinkB=2))

# --- framing + legend --------------------------------------------------------
ax.set_aspect(1.0 / math.cos(math.radians(41.8)))
ax.set_xlim(5.4, 20.4); ax.set_ylim(36.2, 47.4)
ax.set_xlabel("longitude (°E)"); ax.set_ylabel("latitude (°N)")
ax.set_title("SEBD grand tour — optimized path on the map of Italy\n"
             "3,527 km · solid = land leg, dashed = sea crossing (no ferry modelled)",
             fontsize=11)
ax.grid(True, ls=":", lw=0.4, alpha=0.4)
ax.legend(handles=[
    Line2D([], [], marker="*", color="w", markerfacecolor="green",
           markeredgecolor="k", markersize=14, label="start: Gizzeria Lido ’93"),
    Line2D([], [], marker="s", color="w", markerfacecolor="crimson",
           markeredgecolor="k", markersize=10, label="end: Senigallia ’26"),
    Line2D([], [], marker="D", color="w", markerfacecolor="white",
           markeredgecolor=REPEAT, markersize=10, label="repeat venue (hosted ×2)"),
    Line2D([], [], marker="o", color="w", markerfacecolor="#222",
           markersize=7, label="single-host venue"),
    Line2D([], [], color=ROUTE, lw=1.6, label="land leg"),
    Line2D([], [], color=ROUTE, lw=1.6, linestyle=(0, (4, 3)), label="sea crossing"),
], loc="upper right", fontsize=7.4, framealpha=0.96)
fig.tight_layout()
fig.savefig("sebd_route_italy.png", dpi=160)
fig.savefig("sebd_route_italy.svg")
print("wrote sebd_route_italy.png and .svg")
print("unique venues: %d  (from 34 editions)" % len(locs))
print("island venues:", ", ".join("%s [%s]" % (c, m if isinstance(m, str) else "isle")
                                   for c, m in island_venues))
print("sea-crossing legs (different landmasses):")
for a, b in sea_legs:
    print("  %-26s -> %s" % (a, b))
