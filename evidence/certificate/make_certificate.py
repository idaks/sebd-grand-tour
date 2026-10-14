#!/usr/bin/env python3
"""
make_certificate.py -- emit a SOLVER-FREE proof that no SEBD tour is shorter
than 3527 km.

WHY.  exact_tsp.py proves optimality by calling HiGHS six times.  Believing its
answer means believing HiGHS.  This script produces a proof object that a
skeptic can check with integer arithmetic alone -- no LP, no branch-and-bound,
no floating point, no solver.  LPs are used here only to FIND the numbers; the
certificate does not depend on them being optimal, feasible, or even sensible.

THE INEQUALITY.  Model: Hamiltonian cycles on 35 nodes (the 34 editions plus a
zero-cost dummy joined to stops 1 and 34, which turns the path-TSP into a
cycle-TSP of equal cost).  Pick ANY node potentials y_v and ANY cut multipliers
z_S >= 0, and define the reduced cost of an edge

    d_e = c_e - y_u - y_v - sum { z_S : e crosses the boundary of S } .

Then for every Hamiltonian cycle x (branch fixings F1: x_e = 1, F0: x_e = 0):

    cost(x) = sum_e c_e x_e
            = sum_e d_e x_e + sum_v y_v * (degree of v)  + sum_S z_S * |x cap delta(S)|
            = sum_e d_e x_e + 2 sum_v y_v                + sum_S z_S * |x cap delta(S)|
           >= sum_e d_e x_e + 2 sum_v y_v + 2 sum_S z_S           [cut >= 2, z >= 0]
           >= 2 sum_v y_v + 2 sum_S z_S + sum_{e in F1} d_e
                                        + sum_{e free} min(0, d_e)   [x_e in {0,1}]

Every step is elementary: degree is exactly 2, a cycle crosses any proper cut at
least twice, and a 0/1 variable can only hurt where d_e < 0.  No duality theorem
is invoked -- if the y, z were pulled out of a hat the inequality would still
hold; bad ones merely give a useless bound.

THE TREE.  One inequality is not enough: the best bound obtainable this way with
subtour cuts alone is 3447 km, 80 km short.  So the proof is a binary tree that
splits on "edge e is used / is not used"; the two branches are exhaustive by
construction, and each of the 226 leaves carries its own y, z closing that
subproblem above 3526.  All costs are integers, so a bound > 3526 means >= 3527.

OUTPUT.  certificate.pl -- Prolog facts, checked by check_certificate.pl.
All potentials are scaled by 1000 and rounded to integers, so the checker never
leaves integer arithmetic.

Run:  python3 make_certificate.py       (needs scipy; ~2 min)
"""
import sys, os
import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "..", "Claude-artifacts")
sys.path.insert(0, ART)
import trip

D, N = trip.D, trip.N                 # 34 editions, integer km
DUMMY, M = N, N + 1                   # 0-based; DUMMY = index 34 = "node 35"
CLAIM = 3527                          # to prove: every tour >= CLAIM
SCALE = 1000                          # potentials are kept as ints/SCALE

# ---------------------------------------------------------------- the edge set
edges, cost = [], []
for i in range(N):
    for j in range(i + 1, N):
        edges.append((i, j)); cost.append(D[i][j])
edges.append((0, DUMMY));     cost.append(0)      # dummy -- stop 1
edges.append((N - 1, DUMMY)); cost.append(0)      # dummy -- stop 34
E = len(edges)
c = np.array(cost, float)
inc = [[] for _ in range(M)]
for k, (i, j) in enumerate(edges):
    inc[i].append(k); inc[j].append(k)

A_deg = np.zeros((M, E))
for k, (i, j) in enumerate(edges):
    A_deg[i, k] = 1.0; A_deg[j, k] = 1.0
b_deg = 2.0 * np.ones(M)

cuts, cutrows, crosses = [], [], []   # crosses[s] = set of edge ids in delta(S)


def add_cut(S):
    S = frozenset(S)
    if S in cuts or not (2 <= len(S) <= M - 2):
        return False
    r = np.zeros(E); cr = set()
    for k, (i, j) in enumerate(edges):
        if (i in S) != (j in S):
            r[k] = 1.0; cr.add(k)
    cuts.append(S); cutrows.append(r); crosses.append(cr)
    return True


def stoer_wagner(cap):
    """global minimum cut of the fractional support -- exact subtour separation"""
    w = {(min(i, j), max(i, j)): v for (i, j), v in cap.items() if v > 1e-12}
    merged = {v: {v} for v in range(M)}
    best, bestS = float("inf"), None
    active = list(range(M))
    while len(active) > 1:
        a = active[0]; A = [a]
        wts = {v: w.get((min(a, v), max(a, v)), 0.0) for v in active if v != a}
        while len(A) < len(active):
            v = max(wts, key=lambda u: wts[u])
            A.append(v); del wts[v]
            for u in list(wts):
                wts[u] += w.get((min(u, v), max(u, v)), 0.0)
        t, s = A[-1], A[-2]
        ct = sum(w.get((min(t, v), max(t, v)), 0.0) for v in active if v != t)
        if ct < best:
            best, bestS = ct, set(merged[t])
        active.remove(t)
        for v in active:
            if v == s:
                continue
            k1, k2 = (min(s, v), max(s, v)), (min(t, v), max(t, v))
            if k2 in w:
                w[k1] = w.get(k1, 0.0) + w.pop(k2)
        w.pop((min(s, t), max(s, t)), None)
        merged[s] = merged[s] | merged[t]
    return best, bestS


def solve_node(F0, F1):
    lo = np.zeros(E); hi = np.ones(E)
    for k in F0: hi[k] = 0.0
    for k in F1: lo[k] = 1.0
    while True:
        A_ub = -np.array(cutrows) if cuts else None
        b_ub = -2.0 * np.ones(len(cuts)) if cuts else None
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_deg, b_eq=b_deg,
                      bounds=list(zip(lo, hi)), method="highs")
        if not res.success:
            return None
        x = res.x
        val, S = stoer_wagner({edges[k]: x[k] for k in range(E) if x[k] > 1e-9})
        if val > 2.0 - 1e-7:
            return res
        if not (add_cut(S) or add_cut(set(range(M)) - S)):
            return res


def scaled_bound(Y, Z, F0, F1):
    """EXACTLY the arithmetic the Prolog checker will redo: all integers, x SCALE."""
    tot = 2 * sum(Y) + 2 * sum(Z)
    for k, (i, j) in enumerate(edges):
        if k in F0:
            continue
        d = SCALE * int(cost[k]) - Y[i] - Y[j]
        for s in range(len(Z)):
            if k in crosses[s]:
                d -= Z[s]
        if k in F1 or d < 0:
            tot += d
    return tot


THRESH = SCALE * (CLAIM - 1)          # bound > 3526  =>  integral tour >= 3527

# ---------------------------------------------------------------- branch & bound
leaves = []
nodes = 0
stack = [(frozenset(), frozenset(), [])]        # F0, F1, decision path
while stack:
    F0, F1, path = stack.pop()
    nodes += 1
    res = solve_node(F0, F1)
    assert res is not None, "infeasible node -- would need a Farkas certificate"
    Y = [int(round(v * SCALE)) for v in res.eqlin.marginals]
    Z = [max(0, int(round(-v * SCALE))) for v in res.ineqlin.marginals]
    b = scaled_bound(Y, Z, F0, F1)
    if b > THRESH:
        leaves.append((path, Y, Z, b)); continue
    x = res.x
    frac = sorted((abs(x[k] - 0.5), k) for k in range(E)
                  if k not in F0 and k not in F1 and 1e-6 < x[k] < 1 - 1e-6)
    if not frac:                                  # integral: a genuine tour
        val = int(sum(cost[k] for k in range(E) if x[k] > 0.5))
        assert val >= CLAIM, f"found a tour of {val} km -- the claim is FALSE"
        leaves.append((path, Y, Z, SCALE * val)); continue
    k = frac[0][1]
    stack.append((F0 | {k}, F1, path + [(k, 0)]))
    stack.append((F0, F1 | {k}, path + [(k, 1)]))

print(f"nodes {nodes}  leaves {len(leaves)}  cuts {len(cuts)}  "
      f"depth {max(len(p) for p, _, _, _ in leaves)}")

# every leaf must survive re-checking with the FINAL cut pool (z_S = 0 for cuts
# that did not exist yet when the leaf was closed)
for path, Y, Z, b in leaves:
    F0 = frozenset(k for k, v in path if v == 0)
    F1 = frozenset(k for k, v in path if v == 1)
    Zf = Z + [0] * (len(cuts) - len(Z))
    assert scaled_bound(Y, Zf, F0, F1) > THRESH, "leaf does not re-verify"
print("self-check with final cut pool: OK")

# ---------------------------------------------------------------- emit Prolog
out = os.path.join(HERE, "certificate.pl")
with open(out, "w") as f:
    w = f.write
    w("%% certificate.pl -- proof that NO tour of the 34 SEBD editions is shorter\n"
      "%% than 3527 km.  Generated by make_certificate.py; checked (independently\n"
      "%% of any solver, in integer arithmetic) by check_certificate.pl.\n"
      "%%\n"
      "%% Nodes 1..34 = SEBD editions; node 35 = the zero-cost dummy that closes\n"
      "%% the path 1->..->34 into a cycle.  Potentials and multipliers are scaled\n"
      "%% by scale/1 and stored as integers.\n"
      "%%\n"
      "%%   claim(Km).                  the lower bound being proved\n"
      "%%   scale(S).                   y and z are stored as round(S*value)\n"
      "%%   edge(Id, U, V, Km).         the 563 edges of the model\n"
      "%%   cut(Id, Nodes).             a proper node subset S (2 =< |S| =< 33)\n"
      "%%   leaf(Id, Path, Ys, Zs).     Path = [Edge-0|Edge-1,...] branch decisions\n"
      "%%                               Ys   = 35 potentials, nodes 1..35 in order\n"
      "%%                               Zs   = [CutId-Value, ...], nonzero only\n\n")
    w(f"claim({CLAIM}).\nscale({SCALE}).\ndummy(35).\nnode_count({M}).\n")
    w(f"counts(edges({E}), cuts({len(cuts)}), leaves({len(leaves)})).\n\n")
    for k, (i, j) in enumerate(edges):
        w(f"edge({k+1}, {i+1}, {j+1}, {int(cost[k])}).\n")
    w("\n")
    for s, S in enumerate(cuts):
        w(f"cut({s+1}, {sorted(v + 1 for v in S)}).\n")
    w("\n")
    for n, (path, Y, Z, b) in enumerate(leaves):
        p = "[" + ",".join(f"{k+1}-{v}" for k, v in path) + "]"
        zs = "[" + ",".join(f"{s+1}-{z}" for s, z in enumerate(Z) if z != 0) + "]"
        w(f"leaf({n+1}, {p}, {Y}, {zs}).\n")
print(f"wrote {out} ({os.path.getsize(out)} bytes)")
