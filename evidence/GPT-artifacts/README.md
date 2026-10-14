# SEBD trip-planning artifacts

## Distance model

Distances use an **equirectangular planar approximation** derived from latitude
and longitude:

- `x = R × Δlongitude × cos(mean latitude)`
- `y = R × Δlatitude`
- `distance = sqrt(x² + y²)`

with `R = 6371.0088 km`. These are straight-line approximations, not road,
rail, or ferry distances.

The distance table stores each unordered pair once. There are
`34 × 33 / 2 = 561` distance facts.

## Routes

- Chronological route: **15263.9 km**
- Heuristically optimized fixed-endpoint route: **3546.9 km**
- Reduction: **11717.0 km (76.8%)**

The optimized route fixes conference 1 as the start and conference 34 as the
end. Intermediate editions may appear in any order.

The optimization is a high-quality heuristic result obtained using multistart
nearest-neighbor and cheapest-insertion constructions, followed by fixed-endpoint
2-opt and iterated local search. It is **not a mathematical proof of global
optimality**.

## Optimized order by conference number

`1 → 29 → 21 → 25 → 24 → 15 → 26 → 19 → 11 → 16 → 12 → 32 → 28 → 33 → 22 → 3 → 23 → 8 → 27 → 10 → 4 → 30 → 17 → 7 → 13 → 5 → 31 → 20 → 9 → 18 → 2 → 6 → 14 → 34`

## Files

- `sebd_locations.dl`: location facts
- `sebd_distances.dl`: 561 symmetric pairwise distance facts, one orientation only
- `sebd_routes.dl`: route steps, legs, totals, and method
- `sebd_distances.csv`: pairwise distance table
- `sebd_routes.csv`: chronological and optimized route tables
