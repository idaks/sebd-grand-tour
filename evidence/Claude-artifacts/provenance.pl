%% provenance.pl -- meta-provenance: the SEBD experiment as a provenance graph.
%% Steps consume input artifacts and produce output artifacts; artifact-level
%% lineage is the transitive closure.  Companion to meta-provenance.org.
%%
%% Load:  swipl -q -g demo -t halt provenance.pl
%% Try:   ?- why('sebd_route_optimized.png', Sources).
%%        ?- ancestor('route_optimized.pl', X).
%%        ?- produced_by('verify.pl', Step).

:- discontiguous step/2, output/2, input/2, decision/2, check/3.

%% step(Id, Title).
step(s1, 'extract 34 SEBD editions from DBLP').
step(s3, 'sebd.pl: sebd/5 facts + sebd_repeat views').
step(s4, 'sebd.lp: port relation + views to clingo').
step(s5a, 'trip.py: projection + distance/route solver').
step(s5b, 'emit distances, routes, certificate checker').
step(s5c, 'tsp.lp: clingo path-TSP cross-check model').
step(s5d, 'README.org: index + results').
step(s6, 'make_map.py: render the verified route').
step(s8, 'meta-provenance record').
step(s9, 'exact_tsp.py: PROVE optimality (branch-and-cut)').

%% output(Step, Artifact).   input(Step, Artifact).
output(s1, 'sebd-list-34').
input( s1, 'dblp:sebd-index').          input(s1, 'user:senigallia-2026').

output(s3, 'sebd.pl').
input( s3, 'sebd-list-34').             input(s3, 'claude:latlong-estimates').

output(s4, 'sebd.lp').
input( s4, 'sebd.pl').

output(s5a, 'trip.py').
input( s5a, 'sebd.pl').                 input(s5a, 'method:equirectangular-projection').

output(s5b, 'distance.pl').  output(s5b, 'distance.lp').
output(s5b, 'route_inorder.pl').  output(s5b, 'route_optimized.pl').
output(s5b, 'verify.pl').
input( s5b, 'trip.py').

output(s5c, 'tsp.lp').
input( s5c, 'distance.lp').

output(s5d, 'README.org').
input( s5d, 'route_inorder.pl').        input(s5d, 'route_optimized.pl').

output(s6, 'make_map.py').
output(s6, 'sebd_route_optimized.png'). output(s6, 'sebd_route_compare.png').
input( s6, 'route_optimized.pl').       input(s6, 'trip.py').

output(s8, 'meta-provenance.org').  output(s8, 'provenance.pl').
input( s8, 'README.org').

output(s9, 'exact_tsp.py').
input( s9, 'trip.py').                  input(s9, 'route_optimized.pl').

%% decision(Step, What).
decision(s1, 'distrust WebFetch summary; re-derive from raw DBLP HTML').
decision(s3, 'single-quoted atoms so L\'Aquila is safe').
decision(s4, 'coordinates in centidegrees -- clingo has no floats').
decision(s5a, 'integer km; honest metric (triangle inequality holds)').
decision(s5b, 'distance keyed by edition number, not city; store once (I<J)').
decision(s6, 'render the verified order from route_optimized.pl, not a re-solve').
decision(s9, 'lazy subtour-elimination cuts + HiGHS MILP; lower bound meets the tour').

%% check(Step, What, Result).
check(s1, 'count = 34 = 2026-1993+1', pass).
check(s3, 'swipl: 34 facts; repeats Rimini/Venice/Villasimius', pass).
check(s4, 'clingo: single answer set; same three repeats', pass).
check(s5b, 'verify.pl recomputes total from distance/3 = 3541', pass).
check(s5c, 'clingo B&B 7592 km / networkx SA 4596 / ILS cannot beat 3541', corroborating).
check(s6, 'segment-intersection test: 2 hits = duplicate-coordinate twins', pass).
check(s9, 'lower bound 2890..3541 meets a feasible tour; 3541 optimal', proven_optimal).

%% ---- provenance rules ------------------------------------------------------

produced_by(A, S) :- output(S, A).

%% direct artifact lineage: A derives from B if one step produced A using B.
derived(A, B) :- output(S, A), input(S, B).

ancestor(A, B) :- derived(A, B).
ancestor(A, B) :- derived(A, C), ancestor(C, B).

%% base sources: consumed but never produced (the raw roots).
base(A) :- input(_, A), \+ output(_, A).

%% why-provenance: the base sources an artifact ultimately depends on.
why(A, Sources) :- setof(B, (ancestor(A, B), base(B)), Sources).

%% a compact, sorted view of an artifact's full lineage.
lineage(A, Ancestors) :- setof(B, ancestor(A, B), Ancestors).

demo :-
    format("Base sources (roots):~n"),
    forall(base(B), format("  ~w~n", [B])),
    format("~nwhy('sebd_route_optimized.png', Sources):~n"),
    why('sebd_route_optimized.png', Src), format("  ~w~n", [Src]),
    format("~nLineage of route_optimized.pl:~n"),
    lineage('route_optimized.pl', L), format("  ~w~n", [L]).
