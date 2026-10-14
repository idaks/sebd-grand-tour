# Evidence and provenance

This bundle records the data, computational assumptions, executable method,
outputs, and integrity hashes for the SEBD route calculation.

## Claim being supported

Given 34 approximate conference coordinates:

1. The chronological path `1 → 2 → … → 34` has an approximate total length of
   **15,263.9 km**.
2. A fixed-endpoint heuristic path beginning at 1 and ending at 34 has length
   **3,546.9 km**:

   `1 → 29 → 21 → 25 → 24 → 15 → 26 → 19 → 11 → 16 → 12 → 32 → 28 → 33
   → 22 → 3 → 23 → 8 → 27 → 10 → 4 → 30 → 17 → 7 → 13 → 5 → 31 → 20
   → 9 → 18 → 2 → 6 → 14 → 34`

The second result is not an optimality certificate. It is a deterministic,
reproducible heuristic solution.

## Evidence chain

- `sebd_locations.dl` records the input coordinates.
- `reproduce_sebd_trip.py` records the distance function and optimization
  procedure.
- `sebd_distances.dl` records all 561 unordered pairwise distances.
- `sebd_routes.dl` records each route, every leg, the method, and total.
- CSV versions permit independent checking with non-Datalog tools.
- `provenance.json` provides a machine-readable account of assumptions,
  parameters, constraints, and reported results.
- `SHA256SUMS` protects the integrity of the included files.

## Reproduction

From this directory:

```sh
./run.sh
```

The script creates a `reproduced/` directory containing newly computed Datalog
and CSV outputs. Compare those outputs with the included originals.

## Important limitation

The coordinates and metric deliberately abstract away actual transportation.
Distances across water are straight lines, not ferry routes; roads, terrain,
travel time, border constraints, and transport modes are ignored.
