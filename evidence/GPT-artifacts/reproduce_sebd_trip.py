#!/usr/bin/env python3
"""
Reproduce the SEBD straight-line distance table and the two route artifacts.

Distance model:
    Equirectangular planar approximation derived from latitude/longitude.
    This is an approximate Euclidean metric in a locally projected plane,
    not a road, rail, or ferry distance.

Optimization:
    Fixed start = conference 1
    Fixed end   = conference 34
    Visit conferences 2..33 exactly once, in arbitrary order.

    Construction:
      - multistart nearest-neighbor
      - multistart cheapest insertion
      - fixed-endpoint 2-opt
      - seeded iterated local search

The optimized route is a reproducible heuristic result, not a proof of
global optimality.
"""

from pathlib import Path
import csv
import math
import random

ROWS = [
    (1, 1993, "Gizzeria_Lido", 38.96, 16.21),
    (2, 1994, "Rimini", 44.07, 12.57),
    (3, 1995, "Ravello", 40.65, 14.61),
    (4, 1996, "San_Miniato", 43.68, 10.85),
    (5, 1997, "Verona", 45.44, 10.99),
    (6, 1998, "Ancona", 43.62, 13.52),
    (7, 1999, "Como", 45.81, 9.09),
    (8, 2000, "LAquila", 42.35, 13.40),
    (9, 2001, "Venice", 45.44, 12.32),
    (10, 2002, "Portoferraio", 42.81, 10.32),
    (11, 2003, "Cetraro", 39.52, 15.94),
    (12, 2004, "Santa_Margherita_di_Pula", 38.97, 8.97),
    (13, 2005, "Bressanone", 46.72, 11.66),
    (14, 2006, "Portonovo", 43.56, 13.60),
    (15, 2007, "Torre_Canne", 40.84, 17.47),
    (16, 2008, "Mondello", 38.20, 13.33),
    (17, 2009, "Camogli", 44.35, 9.15),
    (18, 2010, "Rimini", 44.07, 12.57),
    (19, 2011, "Maratea", 40.00, 15.72),
    (20, 2012, "Venice", 45.44, 12.32),
    (21, 2013, "Roccella_Ionica", 38.32, 16.40),
    (22, 2014, "Sorrento_Coast", 40.63, 14.38),
    (23, 2015, "Gaeta", 41.21, 13.57),
    (24, 2016, "Ugento", 39.93, 18.16),
    (25, 2017, "Squillace_Lido", 38.78, 16.57),
    (26, 2018, "Castellaneta_Marina", 40.56, 16.93),
    (27, 2019, "Castiglione_della_Pescaia", 42.76, 10.88),
    (28, 2020, "Villasimius", 39.14, 9.52),
    (29, 2021, "Pizzo_Calabro", 38.73, 16.16),
    (30, 2022, "Tirrenia", 43.63, 10.29),
    (31, 2023, "Galzignano_Terme", 45.31, 11.73),
    (32, 2024, "Villasimius", 39.14, 9.52),
    (33, 2025, "Ischia", 40.74, 13.95),
    (34, 2026, "Senigallia", 43.71, 13.22),
]

R_EARTH_KM = 6371.0088
RANDOM_SEED = 20260618
ILS_ITERATIONS = 4000

def atom(text):
    return text.lower().replace("'", "").replace("-", "_")

def loc_atom(row):
    return f"n{row[0]:02d}_{atom(row[2])}"

def distance_km(a, b):
    lat1, lon1 = a[3], a[4]
    lat2, lon2 = b[3], b[4]
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    mean_lat = math.radians((lat1 + lat2) / 2.0)
    x = R_EARTH_KM * dlon * math.cos(mean_lat)
    y = R_EARTH_KM * dlat
    return math.hypot(x, y)

def build_matrix():
    n = len(ROWS)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = distance_km(ROWS[i], ROWS[j])
            matrix[i][j] = matrix[j][i] = d
    return matrix

D = build_matrix()
N = len(ROWS)
START, END = 0, N - 1
INTERNAL = list(range(1, N - 1))

def route_length(route):
    return sum(D[a][b] for a, b in zip(route, route[1:]))

def nearest_neighbor_route(first_choice=None):
    unvisited = set(INTERNAL)
    route = [START]
    current = START
    if first_choice is not None:
        route.append(first_choice)
        unvisited.remove(first_choice)
        current = first_choice
    while unvisited:
        nxt = min(unvisited, key=lambda j: D[current][j])
        route.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    route.append(END)
    return route

def cheapest_insertion_route(seed_node=None):
    remaining = set(INTERNAL)
    if seed_node is None:
        seed_node = min(remaining, key=lambda j: D[START][j] + D[j][END])
    route = [START, seed_node, END]
    remaining.remove(seed_node)
    while remaining:
        best = None
        for node in remaining:
            for pos in range(len(route) - 1):
                a, b = route[pos], route[pos + 1]
                increase = D[a][node] + D[node][b] - D[a][b]
                candidate = (increase, node, pos + 1)
                if best is None or candidate < best:
                    best = candidate
        _, node, pos = best
        route.insert(pos, node)
        remaining.remove(node)
    return route

def two_opt_fixed(route):
    route = route[:]
    improved = True
    while improved:
        improved = False
        best_delta = -1e-12
        best_pair = None
        for i in range(1, len(route) - 2):
            a, b = route[i - 1], route[i]
            for k in range(i + 1, len(route) - 1):
                c, d = route[k], route[k + 1]
                delta = D[a][c] + D[b][d] - D[a][b] - D[c][d]
                if delta < best_delta:
                    best_delta = delta
                    best_pair = (i, k)
        if best_pair is not None:
            i, k = best_pair
            route[i:k + 1] = reversed(route[i:k + 1])
            improved = True
    return route

def optimize():
    candidates = [two_opt_fixed(nearest_neighbor_route())]
    for node in INTERNAL:
        candidates.append(two_opt_fixed(nearest_neighbor_route(node)))
        candidates.append(two_opt_fixed(cheapest_insertion_route(node)))

    best = min(candidates, key=route_length)
    best_length = route_length(best)
    rng = random.Random(RANDOM_SEED)

    for _ in range(ILS_ITERATIONS):
        trial = best[:]
        operation = rng.randrange(3)
        if operation == 0:
            i, k = sorted(rng.sample(range(1, N - 1), 2))
            trial[i:k + 1] = reversed(trial[i:k + 1])
        elif operation == 1:
            i, j = rng.sample(range(1, N - 1), 2)
            trial[i], trial[j] = trial[j], trial[i]
        else:
            i = rng.randrange(1, N - 4)
            k = min(N - 2, i + rng.randrange(3, 8))
            segment = trial[i:k + 1]
            rng.shuffle(segment)
            trial[i:k + 1] = segment

        trial = two_opt_fixed(trial)
        trial_length = route_length(trial)
        if trial_length + 1e-9 < best_length:
            best, best_length = trial, trial_length

    return best

def write_outputs(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    chronological = list(range(N))
    optimized = optimize()

    with (outdir / "sebd_locations.dl").open("w", encoding="utf-8") as f:
        f.write("% Schema: sebd(Number, Year, City, Lat, Long).\n\n")
        for n, year, city, lat, lon in ROWS:
            f.write(f"sebd({n}, {year}, {city}, {lat:.2f}, {lon:.2f}).\n")

    with (outdir / "sebd_distances.dl").open("w", encoding="utf-8") as f:
        f.write("% Schema: distance(LocX, LocY, Kilometers).\n")
        f.write("% Only one orientation of each symmetric pair is stored.\n\n")
        for i in range(N):
            for j in range(i + 1, N):
                f.write(
                    f"distance({loc_atom(ROWS[i])}, {loc_atom(ROWS[j])}, "
                    f"{D[i][j]:.1f}).\n"
                )

    with (outdir / "sebd_routes.dl").open("w", encoding="utf-8") as f:
        f.write("% route_step(Route, Step, Number, Year, City).\n")
        f.write("% route_leg(Route, Step, FromNumber, ToNumber, Kilometers).\n")
        f.write("% route_total(Route, Kilometers).\n")
        f.write("% route_method(Route, Method).\n\n")
        f.write("route_method(chronological, conference_number_order).\n")
        f.write(
            "route_method(optimized, "
            "multistart_nearest_neighbor_cheapest_insertion_2opt_ils).\n\n"
        )
        for name, route in (("chronological", chronological), ("optimized", optimized)):
            for step, idx in enumerate(route, start=1):
                n, year, city, _, _ = ROWS[idx]
                f.write(f"route_step({name}, {step}, {n}, {year}, {city}).\n")
            f.write("\n")
            for step, (a, b) in enumerate(zip(route, route[1:]), start=1):
                f.write(
                    f"route_leg({name}, {step}, {ROWS[a][0]}, {ROWS[b][0]}, "
                    f"{D[a][b]:.1f}).\n"
                )
            f.write(f"route_total({name}, {route_length(route):.1f}).\n\n")

    with (outdir / "sebd_distances.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["FromNumber", "FromCity", "ToNumber", "ToCity", "Kilometers"])
        for i in range(N):
            for j in range(i + 1, N):
                w.writerow([ROWS[i][0], ROWS[i][2], ROWS[j][0], ROWS[j][2],
                            round(D[i][j], 1)])

    with (outdir / "sebd_routes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Route", "Step", "Number", "Year", "City",
                    "NextNumber", "LegKilometers"])
        for name, route in (("chronological", chronological), ("optimized", optimized)):
            for step, idx in enumerate(route, start=1):
                next_idx = route[step] if step < len(route) else None
                w.writerow([
                    name, step, ROWS[idx][0], ROWS[idx][1], ROWS[idx][2],
                    ROWS[next_idx][0] if next_idx is not None else "",
                    round(D[idx][next_idx], 1) if next_idx is not None else "",
                ])

    print(f"Chronological total: {route_length(chronological):.1f} km")
    print(f"Optimized total:     {route_length(optimized):.1f} km")
    print("Optimized order:     " +
          " -> ".join(str(ROWS[i][0]) for i in optimized))

if __name__ == "__main__":
    write_outputs(Path("reproduced"))
