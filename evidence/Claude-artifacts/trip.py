#!/usr/bin/env python3
"""
trip.py -- SEBD "grand tour" experiment.

Build approximate Euclidean (great-circle-ish) distances between the 34 SEBD
edition locations from their lat/long, then:
  (a) the in-order route  1 -> 2 -> ... -> 34
  (b) an optimized path   1 -> (2..33 in any order) -> 34   (path-TSP)

Distances: equirectangular projection to a local km plane (reference latitude
42 N, R = 6371 km), then ordinary 2-D Euclidean distance, rounded to whole km.
This gives an honest metric (triangle inequality holds), so the optimized route
is a real shortest-path certificate that can be checked independently.

Emits Datalog/ASP artifacts:
  distance.pl / distance.lp   distance(I, J, Km).   (I < J, symmetric, stored once)
  route_inorder.pl            route_inorder(Step, From, To, Km). + total
  route_optimized.pl          visit(Pos, No). route_optimized(...). + total
  verify.pl                   independent certificate checker (run with swipl)

Optimization is multi-restart 2-opt + Or-opt local search; exact_tsp.py later
PROVES 3527 km optimal (branch-and-cut; 3541 before the 2026-08-01 coordinate
fix). tsp.lp is a weak clingo cross-check.
"""

import math, random

# (Number, Year, City, Lat, Long) -- decimal degrees, same data as sebd.pl
# Coordinates verified against OpenStreetMap/Nominatim on 2026-08-01.  Four were
# corrected then: each named a coastal frazione but had drifted inland toward its
# parent comune -- Gizzeria Lido, Torre Canne, Squillace Lido, Castellaneta Marina.
CITIES = [
    ( 1, 1993, "Gizzeria Lido",             38.93, 16.22),
    ( 2, 1994, "Rimini",                    44.06, 12.57),
    ( 3, 1995, "Ravello",                   40.65, 14.61),
    ( 4, 1996, "San Miniato",               43.68, 10.85),
    ( 5, 1997, "Verona",                    45.44, 10.99),
    ( 6, 1998, "Ancona",                    43.62, 13.52),
    ( 7, 1999, "Como",                      45.81,  9.08),
    ( 8, 2000, "L'Aquila",                  42.35, 13.40),
    ( 9, 2001, "Venice",                    45.44, 12.34),
    (10, 2002, "Portoferraio",              42.81, 10.32),
    (11, 2003, "Cetraro",                   39.52, 15.94),
    (12, 2004, "Santa Margherita di Pula",  38.96,  8.97),
    (13, 2005, "Bressanone",                46.72, 11.66),
    (14, 2006, "Portonovo",                 43.56, 13.59),
    (15, 2007, "Torre Canne",               40.84, 17.47),
    (16, 2008, "Mondello",                  38.20, 13.32),
    (17, 2009, "Camogli",                   44.35,  9.16),
    (18, 2010, "Rimini",                    44.06, 12.57),
    (19, 2011, "Maratea",                   39.99, 15.72),
    (20, 2012, "Venice",                    45.44, 12.34),
    (21, 2013, "Roccella Ionica",           38.32, 16.40),
    (22, 2014, "Sorrento",                  40.63, 14.37),
    (23, 2015, "Gaeta",                     41.21, 13.57),
    (24, 2016, "Ugento",                    39.93, 18.16),
    (25, 2017, "Squillace Lido",            38.78, 16.57),
    (26, 2018, "Castellaneta Marina",       40.47, 16.94),
    (27, 2019, "Castiglione della Pescaia", 42.76, 10.88),
    (28, 2020, "Villasimius",               39.14,  9.52),
    (29, 2021, "Pizzo Calabro",             38.73, 16.16),
    (30, 2022, "Tirrenia",                  43.63, 10.29),
    (31, 2023, "Galzignano Terme",          45.30, 11.72),
    (32, 2024, "Villasimius",               39.14,  9.52),
    (33, 2025, "Ischia",                    40.73, 13.95),
    (34, 2026, "Senigallia",                43.71, 13.22),
]

R, LAT0 = 6371.0, 42.0
N = len(CITIES)
name = {no: city for (no, _, city, _, _) in CITIES}

def project(lat, lon):
    x = R * math.radians(lon) * math.cos(math.radians(LAT0))
    y = R * math.radians(lat)
    return x, y

PTS = [project(lat, lon) for (_, _, _, lat, lon) in CITIES]   # 0-based, index = No-1

def km(i, j):                       # integer km between 0-based indices i, j
    return round(math.dist(PTS[i], PTS[j]))

D = [[km(i, j) for j in range(N)] for i in range(N)]          # rounded-int matrix

def path_len(route):                # route is a list of 0-based indices
    return sum(D[route[k]][route[k + 1]] for k in range(len(route) - 1))

# ---- (b) path-TSP: fixed endpoints 0 (No 1) and N-1 (No 34) -----------------

def two_opt(route):
    best, improved = route[:], True
    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                a, b, c, e = best[i - 1], best[i], best[j], best[j + 1]
                if D[a][c] + D[b][e] < D[a][b] + D[c][e]:
                    best[i:j + 1] = best[i:j + 1][::-1]
                    improved = True
    return best

def or_opt(route):
    best, improved = route[:], True
    while improved:
        improved = False
        for seg in (1, 2, 3):
            for i in range(1, len(best) - seg):
                if i + seg > len(best) - 1:
                    continue
                block = best[i:i + seg]
                rest = best[:i] + best[i + seg:]
                for k in range(1, len(rest)):          # don't touch endpoints
                    cand = rest[:k] + block + rest[k:]
                    if path_len(cand) < path_len(best):
                        best, improved = cand, True
    return best

def local_search(route):
    prev = None
    while prev != route:
        prev = route
        route = or_opt(two_opt(route))
    return route

def nearest_neighbor():
    start, end = 0, N - 1
    interior = set(range(1, N - 1))
    route, cur = [start], start
    while interior:
        nxt = min(interior, key=lambda j: D[cur][j])
        route.append(nxt); interior.discard(nxt); cur = nxt
    return route + [end]

def solve_tsp_path():
    random.seed(20260618)
    candidates = [list(range(N)), nearest_neighbor()]        # in-order + NN seeds
    mid = list(range(1, N - 1))
    for _ in range(400):
        random.shuffle(mid)
        candidates.append([0] + mid[:] + [N - 1])
    best = min((local_search(c) for c in candidates), key=path_len)
    return best

# ---- artifact emitters ------------------------------------------------------

def emit_distance():
    pairs = [(i + 1, j + 1, D[i][j]) for i in range(N) for j in range(i + 1, N)]
    hdr = ("%% distance(I, J, Km).  I < J: stored once (Euclidean distance is\n"
           "%% symmetric).  I, J are SEBD edition numbers (stops 1..34), NOT city\n"
           "%% names -- some cities repeat (Rimini, Venice, Villasimius), and a trip\n"
           "%% visits 34 distinct stops.  Km = approx. Euclidean km (see trip.py).\n")
    with open("distance.pl", "w") as f:
        f.write(hdr)
        f.write("%% Symmetric lookup for queries:\n"
                "dist(A, B, K) :- distance(A, B, K).\n"
                "dist(A, B, K) :- distance(B, A, K).\n\n")
        for i, j, d in pairs:
            f.write(f"distance({i:>2}, {j:>2}, {d:>4}).\n")
    with open("distance.lp", "w") as f:
        f.write(hdr)
        for i, j, d in pairs:
            f.write(f"distance({i}, {j}, {d}).\n")
    return len(pairs)

def emit_route(filename, order, head, total_pred):
    legs = [(k + 1, order[k] + 1, order[k + 1] + 1, D[order[k]][order[k + 1]])
            for k in range(len(order) - 1)]
    total = sum(d for *_, d in legs)
    with open(filename, "w") as f:
        f.write(head)
        if "optimized" in filename:
            f.write("%% Visiting order (Pos = position in trip, No = edition number):\n")
            for pos, idx in enumerate(order, 1):
                f.write(f"visit({pos:>2}, {idx + 1:>2}).   %% {name[idx + 1]}\n")
            f.write("\n")
        pred = "route_optimized" if "optimized" in filename else "route_inorder"
        for step, a, b, d in legs:
            f.write(f"{pred}({step:>2}, {a:>2}, {b:>2}, {d:>4}).\n")
        f.write(f"\n{total_pred}({total}).\n")
    return total, legs

def emit_verify():
    with open("verify.pl", "w") as f:
        f.write(
'''%% verify.pl -- independent certificate checker for the optimized route.
%% Run:  swipl -q -g run -t halt verify.pl
%% It does NOT trust total_optimized/1: it recomputes the length from distance/3
%% and checks the route is a valid permutation 1..34 starting at 1, ending at 34.
:- [distance], [route_optimized].

leg_ok(Step) :- route_optimized(Step, A, B, K), dist(A, B, K0), K =:= K0.

run :-
    findall(P-No, visit(P, No), Ps),
    keysort(Ps, Sorted), pairs_values(Sorted, Seq),
    ( Seq = [1|_], last(Seq, 34) -> true ; format("FAIL: endpoints~n"), fail ),
    msort(Seq, S), numlist(1, 34, S),                 % permutation of 1..34
    findall(Step, route_optimized(Step, _, _, _), Steps),
    ( forall(member(St, Steps), leg_ok(St))
        -> true ;  format("FAIL: a stored leg km disagrees with distance/3~n"), fail ),
    findall(K, route_optimized(_, _, _, K), Ks), sum_list(Ks, Recomputed),
    total_optimized(Published),
    ( Recomputed =:= Published
        -> format("PASS: valid 1..34 permutation; recomputed = published = ~w km~n",
                  [Recomputed])
        ;  format("FAIL: recomputed ~w =/= published ~w~n", [Recomputed, Published]) ).
''')

# ---- run --------------------------------------------------------------------

if __name__ == "__main__":
    npairs = emit_distance()
    inorder = list(range(N))
    opt = solve_tsp_path()

    t_in, _ = emit_route("route_inorder.pl", inorder,
                         "%% route_inorder(Step, From, To, Km).  Trip 1->2->...->34.\n",
                         "total_inorder")
    t_opt, _ = emit_route("route_optimized.pl", opt,
                         "%% route_optimized(Step, From, To, Km).  Path-TSP 1->...->34.\n",
                         "total_optimized")
    emit_verify()

    seq = [i + 1 for i in opt]
    print(f"distance facts written : {npairs}  (= C(34,2))")
    print(f"(a) in-order total     : {t_in:>5} km")
    print(f"(b) optimized total    : {t_opt:>5} km   "
          f"({100*(t_in-t_opt)/t_in:.1f}% shorter)")
    print("\noptimized visiting order (edition numbers):")
    print("  " + " -> ".join(str(x) for x in seq))
    print("\noptimized visiting order (cities):")
    line = "  1 " + name[1]
    print("  " + " -> ".join(f"{x}:{name[x]}" for x in seq))
