#!/usr/bin/env python3
"""
make_map.py -- render the SEBD trip on the projected km plane.
Reads the *verified* optimized order from route_optimized.pl (visit/2), so the
picture matches the certificate checked by verify.pl.

Outputs:
  sebd_route_optimized.png   the optimized path 1 -> ... -> 34
  sebd_route_compare.png     in-order (left) vs optimized (right), side by side
"""
import re, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import trip                                   # CITIES, project, path_len, D, N, name

N, name = trip.N, trip.name
# projected km plane (same projection used for distances), origin at SW corner
P = [trip.project(lat, lon) for (_, _, _, lat, lon) in trip.CITIES]
minx = min(x for x, _ in P); miny = min(y for _, y in P)
XY = [(x - minx, y - miny) for x, y in P]     # 0-based index = No-1
X = [p[0] for p in XY]; Y = [p[1] for p in XY]

# read the verified visiting order from route_optimized.pl
pos2no = {}
for line in open("route_optimized.pl"):
    m = re.match(r"\s*visit\(\s*(\d+),\s*(\d+)\)", line)
    if m:
        pos2no[int(m.group(1))] = int(m.group(2))
opt = [pos2no[p] - 1 for p in sorted(pos2no)]        # 0-based optimized order
inorder = list(range(N))                              # 1,2,...,34

def draw(ax, order, title, color):
    xs = [X[i] for i in order]; ys = [Y[i] for i in order]
    ax.plot(xs, ys, "-", color=color, lw=1.4, alpha=0.85, zorder=1)
    ax.scatter(X, Y, s=26, color="#333", zorder=2)
    # start / end markers
    s, e = order[0], order[-1]
    ax.scatter([X[s]], [Y[s]], s=130, marker="*", color="green", zorder=4,
               edgecolor="k", linewidth=0.4, label="start (1) Gizzeria Lido")
    ax.scatter([X[e]], [Y[e]], s=110, marker="s", color="crimson", zorder=4,
               edgecolor="k", linewidth=0.4, label="end (34) Senigallia")
    for i in range(N):                                # edition-number labels
        ax.annotate(str(i + 1), (X[i], Y[i]), textcoords="offset points",
                    xytext=(3, 3), fontsize=6.5, color="#222")
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("east (km)"); ax.set_ylabel("north (km)")
    ax.grid(True, ls=":", lw=0.4, alpha=0.5)
    ax.legend(loc="lower right", fontsize=7, framealpha=0.9)

t_in = trip.path_len(inorder)
t_opt = trip.path_len(opt)

# --- standalone optimized map ---
fig, ax = plt.subplots(figsize=(6.2, 7.4))
draw(ax, opt, f"SEBD grand tour — optimized path\n{t_opt:,} km "
              f"({100*(t_in-t_opt)/t_in:.0f}% shorter than in-order)", "#1f6fb2")
fig.tight_layout(); fig.savefig("sebd_route_optimized.png", dpi=160)

# --- side-by-side comparison ---
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 7.2), sharex=True, sharey=True)
draw(a1, inorder, f"(a) in order 1→…→34\n{t_in:,} km", "#e08214")
draw(a2, opt,     f"(b) optimized 1→…→34\n{t_opt:,} km", "#1f6fb2")
fig.suptitle("34 SEBD editions (1993 Gizzeria Lido → 2026 Senigallia) · "
             "straight-line km, ignores roads/ferries", fontsize=10)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig("sebd_route_compare.png", dpi=160)

print(f"wrote sebd_route_optimized.png  and  sebd_route_compare.png")
print(f"in-order {t_in} km   optimized {t_opt} km")
