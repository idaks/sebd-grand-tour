%% check_certificate.pl -- verify, WITHOUT ANY SOLVER, that 3527 km is optimal.
%%
%% Run (from this directory):   swipl -q -g run -t halt check_certificate.pl
%%
%% What it trusts: SWI-Prolog's integer arithmetic, and nothing else.  No LP, no
%% branch-and-bound, no floating point, no HiGHS, no Python.  The numbers in
%% certificate.pl could have been produced by a solver, by hand, or by a liar --
%% the check below is valid either way; bad numbers simply fail it.
%%
%% What it proves, in six parts:
%%   (1) the model's 563 edges are exactly the 561 published distances plus the
%%       two zero-cost dummy edges  (so the proof is about THIS distance table);
%%   (2) node 35 has exactly two incident edges, both free -- hence every
%%       Hamiltonian cycle of the model uses both, and deleting them leaves a
%%       Hamiltonian path 1 -> ... -> 34 of equal cost, and conversely;
%%   (3) every cut set is a proper subset, 2 =< |S| =< 33, so "a cycle crosses
%%       delta(S) at least twice" is true of every tour;
%%   (4) the 226 leaves form a COMPLETE binary tree over "edge used / not used"
%%       decisions -- i.e. the case analysis is exhaustive;
%%   (5) each leaf's potentials give, by the inequality below, a bound > 3526 km
%%       for every tour obeying that leaf's decisions.  Costs are integers, so
%%       every tour is >= 3527 km;
%%   (6) the published route is a valid 1..34 permutation of length exactly
%%       3527 km.  Lower bound = upper bound = optimum.
%%
%% The inequality (leaf L, decisions F1: x_e = 1, F0: x_e = 0):
%%
%%   d_e  =  c_e - y_u - y_v - sum { z_S : edge e crosses cut S }
%%   cost(x)  >=  2*sum_v y_v + 2*sum_S z_S
%%                 + sum over e in F1 of d_e
%%                 + sum over free e of min(0, d_e)
%%
%% for ANY y and ANY z >= 0.  Proof: substitute d_e back, then use degree = 2
%% exactly, |x cap delta(S)| >= 2 with z_S >= 0, and 0 =< x_e =< 1.  Everything
%% here is scaled by scale/1 so it stays in integers.

:- ['certificate'].
:- ['../Claude-artifacts/distance'].
:- ['../Claude-artifacts/route_optimized'].

:- dynamic crosses/2, ycheck/1.

%% ---------------------------------------------------------------- (1) the edges
check_edges :-
    counts(edges(NE), _, _),
    findall(I, edge(I, _, _, _), Is), length(Is, NE),
    ( forall(edge(_, U, V, K),
             ( V =:= 35 -> memberchk(U, [1, 34]), K =:= 0
             ; U < V, dist(U, V, K) ))
      -> true ; format("FAIL: an edge disagrees with distance.pl~n"), fail ),
    findall(U-V, (between(1, 33, U), U1 is U + 1, between(U1, 34, V)), Pairs),
    ( forall(member(U-V, Pairs), edge(_, U, V, _))
      -> true ; format("FAIL: a pair of editions has no edge~n"), fail ),
    length(Pairs, NP), NR is NE - NP,
    format("PASS (1) ~w edges = ~w published distances + ~w dummy edges~n",
           [NE, NP, NR]).

%% ------------------------------------------------- (2) path <-> cycle, honestly
check_dummy :-
    dummy(Dm),
    findall(U-K, edge(_, U, Dm, K), Ds), msort(Ds, Sorted),
    ( Sorted = [1-0, 34-0]
      -> format("PASS (2) node ~w joins only stops 1 and 34, at zero cost~n", [Dm])
      ;  format("FAIL: dummy node is not the intended path-closing device~n"), fail ).

%% ----------------------------------------------------------------- (3) the cuts
check_cuts :-
    counts(_, cuts(NC), _), node_count(M), Hi is M - 2,
    ( forall(cut(_, S),
             ( sort(S, S), length(S, L), L >= 2, L =< Hi,
               forall(member(V, S), (integer(V), V >= 1, V =< M)) ))
      -> format("PASS (3) all ~w cuts are proper subsets (2 =< |S| =< ~w)~n", [NC, Hi])
      ;  format("FAIL: a cut set is not a proper subset~n"), fail ).

%% ------------------------------------------------- (4) the case analysis is total
%  A set of decision paths is exhaustive iff it is a complete binary tree: either
%  it is the single empty path, or every path starts with a decision on the SAME
%  edge, both values occur, and each half is exhaustive.
complete([[]]) :- !.
complete(Paths) :-
    Paths = [[E-_|_]|_],
    findall(P, (member([E-0|P], Paths)), Zs),
    findall(P, (member([E-1|P], Paths)), Os),
    length(Paths, N), length(Zs, NZ), length(Os, NO), N =:= NZ + NO,
    NZ > 0, NO > 0,
    complete(Zs), complete(Os).

check_tree :-
    findall(P, leaf(_, P, _, _), Paths), length(Paths, N),
    ( complete(Paths)
      -> format("PASS (4) the ~w leaves form a complete binary tree -- exhaustive~n", [N])
      ;  format("FAIL: the case analysis has a hole~n"), fail ).

%% ------------------------------------------------------------- (5) the leaf bounds
index_cuts :-
    retractall(crosses(_, _)),
    forall(edge(I, U, V, _),
           ( findall(S, (cut(S, Set), memberchk(U, Set), \+ memberchk(V, Set)), A),
             findall(S, (cut(S, Set), memberchk(V, Set), \+ memberchk(U, Set)), B),
             append(A, B, C), sort(C, Cs), assertz(crosses(I, Cs)) )).

zsum([], _, 0).
zsum([S|Ss], Zt, Sum) :- arg(S, Zt, V), zsum(Ss, Zt, R), Sum is R + V.

edge_term(_, _, _, _, [], 0).
edge_term(Sc, Yt, Zt, F1, [I-U-V-C|Es], Tot) :-
    arg(U, Yt, YU), arg(V, Yt, YV),
    crosses(I, Cs), zsum(Cs, Zt, ZS),
    Dm is Sc * C - YU - YV - ZS,
    ( memberchk(I, F1) -> Add = Dm ; Dm < 0 -> Add = Dm ; Add = 0 ),
    edge_term(Sc, Yt, Zt, F1, Es, Rest),
    Tot is Rest + Add.

leaf_ok(Edges, Thresh, Sc, Id) :-
    leaf(Id, Path, Ys, Zs),
    counts(_, cuts(NC), _),
    findall(I, member(I-0, Path), F0), sort(F0, F0s),
    findall(I, member(I-1, Path), F1), sort(F1, F1s),
    Yt =.. [y|Ys],
    length(Zl, NC), maplist(=(0), Zl), fill_z(Zs, Zl, Zl2), Zt =.. [z|Zl2],
    forall(member(_-Z, Zs), Z >= 0),                    % multipliers nonnegative
    exclude([I-_-_-_]>>memberchk(I, F0s), Edges, Free), % dropped edges contribute 0
    edge_term(Sc, Yt, Zt, F1s, Free, Red),
    sum_list(Ys, SY), sum_list(Zl2, SZ),
    Bound is 2 * SY + 2 * SZ + Red,
    Bound > Thresh.

fill_z([], L, L).
fill_z([S-V|T], L0, L) :- nth1(S, L1, V, Rest), nth1(S, L0, _, Rest), fill_z(T, L1, L).

check_leaves :-
    scale(Sc), claim(Cl), counts(_, _, leaves(NL)),
    Thresh is Sc * (Cl - 1), Lo is Cl - 1,
    findall(I-U-V-C, edge(I, U, V, C), Edges),
    index_cuts,
    ( forall(between(1, NL, Id), leaf_ok(Edges, Thresh, Sc, Id))
      -> format("PASS (5) all ~w leaves bound every tour above ~w km, so >= ~w km~n",
                [NL, Lo, Cl])
      ;  format("FAIL: a leaf does not close~n"), fail ).

%% ----------------------------------------------------------- (6) the upper bound
check_tour :-
    claim(Cl),
    findall(P-No, visit(P, No), Ps), keysort(Ps, S), pairs_values(S, Seq),
    Seq = [1|_], last(Seq, 34),
    msort(Seq, M), numlist(1, 34, M),
    tour_len(Seq, Len),
    ( Len =:= Cl
      -> format("PASS (6) the published route is a valid 1..34 tour of ~w km~n", [Len])
      ;  format("FAIL: published route is ~w km, claim is ~w~n", [Len, Cl]), fail ).

tour_len([_], 0).
tour_len([A, B|T], L) :- dist(A, B, K), tour_len([B|T], R), L is R + K.

%% ---------------------------------------------------------------------- verdict
run :-
    claim(Cl),
    ( check_edges, check_dummy, check_cuts, check_tree, check_leaves, check_tour
      -> format("~nVERIFIED: no tour of the 34 SEBD editions is shorter than ~w km,~n", [Cl]),
         format("and a tour of exactly ~w km exists.  ~w km is optimal.~n", [Cl, Cl])
      ;  format("~nNOT VERIFIED.~n"), fail ).
