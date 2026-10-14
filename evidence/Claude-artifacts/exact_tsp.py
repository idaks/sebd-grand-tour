#!/usr/bin/env python3
"""
exact_tsp.py -- PROVE optimality of the SEBD path-TSP (stop 1 -> ... -> stop 34).

Exact branch-and-cut with scipy.optimize.milp (HiGHS):
  - binary edge variables x_e
  - degree-2 at every node
  - path 1..34 modelled as a Hamiltonian cycle on the real nodes + a dummy node
    joined to the two endpoints by zero-cost edges (degree-2 forces both to be used,
    so the cycle = the path + two free edges; min cycle cost = min path cost)
  - subtour-elimination constraints added lazily until the solution is one tour.
Each milp() call is solved to proven optimality; when the relaxation optimum is a
single tour it is also feasible for the full TSP, hence the exact optimum (and a
valid lower bound). Uses the SAME integer-km matrix as distance.pl / route_*.pl.
"""
import re, numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
import trip

D, N = trip.D, trip.N                 # 34 real nodes (index = edition no - 1), integer km
DUMMY = N                             # node 34 (0-based) = dummy
M = N + 1

edges, cost = [], []
for i in range(N):
    for j in range(i + 1, N):
        edges.append((i, j)); cost.append(D[i][j])
edges.append((0, DUMMY));     cost.append(0)     # dummy -- stop 1
edges.append((N - 1, DUMMY)); cost.append(0)     # dummy -- stop 34
E = len(edges)
cost = np.array(cost, float)

inc = [[] for _ in range(M)]
for e, (i, j) in enumerate(edges):
    inc[i].append(e); inc[j].append(e)
A_deg = np.zeros((M, E))
for v in range(M):
    for e in inc[v]:
        A_deg[v, e] = 1.0
cons = [LinearConstraint(A_deg, 2, 2)]           # degree exactly 2 everywhere
integ = np.ones(E); bnds = Bounds(0, 1)

def components(sel):
    adj = {v: [] for v in range(M)}
    for i, j in sel:
        adj[i].append(j); adj[j].append(i)
    seen, comps = set(), []
    for s in range(M):
        if s in seen:
            continue
        stack, comp = [s], []
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u); comp.append(u)
            stack += [w for w in adj[u] if w not in seen]
        comps.append(comp)
    return comps

it = 0
while True:
    it += 1
    res = milp(c=cost, constraints=cons, integrality=integ, bounds=bnds)
    assert res.success, res.message
    sel = [edges[e] for e in range(E) if res.x[e] > 0.5]
    comps = components(sel)
    print(f"  iter {it:2d}: cost {res.fun:8.1f}  subtours {len(comps)}")
    if len(comps) == 1:
        break
    for S in comps:                              # eliminate every proper subtour
        if len(S) < M:
            Sset = set(S)
            row = np.array([1.0 if (i in Sset and j in Sset) else 0.0
                            for (i, j) in edges])
            cons.append(LinearConstraint(row, 0, len(S) - 1))

opt = res.fun
# recover the path 1..34 from the optimal cycle
adj = {v: [] for v in range(M)}
for i, j in sel:
    adj[i].append(j); adj[j].append(i)
path, prev, cur = [], DUMMY, 0                   # start at stop 1 (index 0), came from dummy
while True:
    path.append(cur)
    nxt = [w for w in adj[cur] if w != prev][0]
    if nxt == DUMMY:
        break
    prev, cur = cur, nxt
order = [p + 1 for p in path]                    # back to edition numbers
length = sum(D[path[k]][path[k+1]] for k in range(len(path)-1))

# the heuristic tour we are checking
pos2no = {}
for line in open("route_optimized.pl"):
    m = re.match(r"\s*visit\(\s*(\d+),\s*(\d+)\)", line)
    if m:
        pos2no[int(m.group(1))] = int(m.group(2))
heur = [pos2no[p] for p in sorted(pos2no)]
heur_len = sum(D[heur[k]-1][heur[k+1]-1] for k in range(len(heur)-1))

print("\n=== EXACT RESULT ===")
print(f"proven optimum (lower = upper bound): {opt:.0f} km")
print(f"recovered optimal path length check : {length} km   (start {order[0]}, end {order[-1]})")
print(f"heuristic tour (route_optimized.pl) : {heur_len} km")
print(f"==> heuristic is OPTIMAL: {heur_len == opt}")
print("optimal order:", " ".join(map(str, order)))
