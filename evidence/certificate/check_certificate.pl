%% check_certificate.pl -- verify, WITHOUT ANY SOLVER, that 3527 km is optimal.
%%
%% Run (from this directory):   swipl -q -g run -t halt check_certificate.pl
%%
%% What it trusts: SWI-Prolog's integer arithmetic, and nothing else.  No LP, no
%% branch-and-bound, no floating point, no HiGHS, no Python.  The numbers in
%% certificate.pl could have been produced by a solver, by hand, or by a liar --
%% the check below is valid either way; bad numbers simply fail it.
%%
%% Hardened 2026-10-16 after an independent review (OpenAI Codex) showed that the
%% 2026-08-04 version accepted a FORGED certificate: a 36th "potential" for a node
%% that does not exist inflated every leaf's bound, and the checker never noticed.
%% The inequality was fine; the checker did not enforce its preconditions.  Now:
%%   - certificate.pl is READ AS DATA, term by term, against a fixed list of
%%     allowed facts -- it can no longer define or redefine any predicate;
%%   - the model's size (35 nodes, dummy node 35, 563 edges) is fixed HERE, not
%%     taken from the certificate it is supposed to check;
%%   - check (0) below enforces the shape of every fact before (1)-(6) run.
%% The original is kept in original-2026-08-04/; see CORRECTIONS.org.
%%
%% What it proves, in seven parts:
%%   (0) the certificate is well-formed: one integer claim and scale > 0;
%%       unique edge, cut and leaf ids; leaf ids exactly 1..N; every leaf has
%%       exactly 35 integer potentials, nonnegative integer multipliers on
%%       existing cuts (each at most once), and decisions on existing edges
%%       (each at most once, value 0 or 1);
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

:- ['../Claude-artifacts/distance'].
:- ['../Claude-artifacts/route_optimized'].

:- dynamic crosses/2, ycheck/1.
:- dynamic claim/1, scale/1, dummy/1, node_count/1, counts/3, edge/4, cut/2, leaf/4.

%% The model, fixed by the checker -- NOT read from the certificate.
model_nodes(35).                 % 34 editions + the dummy node
model_dummy(35).
model_edges(563).                % 34*33/2 = 561 pairs + 2 dummy edges

%% ------------------------------------------------- loading the certificate as data
allowed(claim(_)). allowed(scale(_)). allowed(dummy(_)). allowed(node_count(_)).
allowed(counts(_, _, _)). allowed(edge(_, _, _, _)). allowed(cut(_, _)).
allowed(leaf(_, _, _, _)).

load_certificate :-
    setup_call_cleanup(open('certificate.pl', read, In),
                       read_facts(In), close(In)).
read_facts(In) :-
    read_term(In, T, []),
    (   T == end_of_file -> true
    ;   allowed(T), ground(T) -> assertz(T), read_facts(In)
    ;   format("FAIL: certificate.pl contains a term that is not an allowed fact:~n  ~q~n", [T]),
        fail ).

%% ------------------------------------------------- (0) the certificate's shape
one(G) :- findall(G, G, [G]).
pos_int(X) :- integer(X), X > 0.
unique_ids(Ids) :- msort(Ids, S), sort(Ids, S).

check_shape :-
    model_nodes(M), model_dummy(Dm), model_edges(NE),
    ( one(claim(Cl)), pos_int(Cl), one(scale(Sc)), pos_int(Sc),
      one(dummy(D)), D == Dm, one(node_count(N)), N == M,
      one(counts(Ec, cuts(NC), leaves(NL))), Ec == edges(NE), pos_int(NC), pos_int(NL)
      -> true ; format("FAIL: (0) claim/scale/model size/counts are not as fixed by the checker~n"), fail ),
    ( findall(I, edge(I, _, _, _), EIs), length(EIs, NE), unique_ids(EIs)
      -> true ; format("FAIL: (0) edge ids are not ~w distinct ids~n", [NE]), fail ),
    ( forall(edge(I, U, V, K), (maplist(integer, [I, U, V, K]), K >= 0))
      -> true ; format("FAIL: (0) an edge is not integer-valued~n"), fail ),
    ( findall(S, cut(S, _), CIs), length(CIs, NC), unique_ids(CIs)
      -> true ; format("FAIL: (0) cut ids are not ~w distinct ids~n", [NC]), fail ),
    ( findall(L, leaf(L, _, _, _), LIs), length(LIs, NL), msort(LIs, LS), numlist(1, NL, LS)
      -> true ; format("FAIL: (0) leaf ids are not exactly 1..~w~n", [NL]), fail ),
    ( forall(leaf(_, P, Ys, Zs), leaf_shape(M, NE, P, Ys, Zs))
      -> true ; format("FAIL: (0) a leaf is malformed~n"), fail ),
    format("PASS (0) well-formed: ~w nodes, ~w edges, ~w cuts, ~w leaves, ~w potentials each~n",
           [M, NE, NC, NL, M]).

leaf_shape(M, NE, Path, Ys, Zs) :-
    is_list(Ys), length(Ys, M), maplist(integer, Ys),
    is_list(Zs), pairs_keys_values(Zs, ZK, ZV), unique_ids(ZK),
    forall(member(S, ZK), cut(S, _)),
    forall(member(Z, ZV), (integer(Z), Z >= 0)),
    is_list(Path), pairs_keys_values(Path, PE, PB), unique_ids(PE),
    forall(member(E, PE), (integer(E), E >= 1, E =< NE, edge(E, _, _, _))),
    forall(member(B, PB), memberchk(B, [0, 1])).

%% ---------------------------------------------------------------- (1) the edges
check_edges :-
    model_edges(NE), model_dummy(Dm),
    findall(I, edge(I, _, _, _), Is), length(Is, NE),
    ( forall(edge(_, U, V, K),
             ( V =:= Dm -> memberchk(U, [1, 34]), K =:= 0
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
    model_dummy(Dm),
    findall(U-K, edge(_, U, Dm, K), Ds), msort(Ds, Sorted),
    ( Sorted = [1-0, 34-0]
      -> format("PASS (2) node ~w joins only stops 1 and 34, at zero cost~n", [Dm])
      ;  format("FAIL: dummy node is not the intended path-closing device~n"), fail ).

%% ----------------------------------------------------------------- (3) the cuts
check_cuts :-
    counts(_, cuts(NC), _), model_nodes(M), Hi is M - 2,
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
    ( load_certificate -> true ; format("~nNOT VERIFIED.~n"), fail ),
    ( check_shape -> true ; format("~nNOT VERIFIED.~n"), fail ),
    claim(Cl),
    ( check_edges, check_dummy, check_cuts, check_tree, check_leaves, check_tour
      -> format("~nVERIFIED: no tour of the 34 SEBD editions is shorter than ~w km,~n", [Cl]),
         format("and a tour of exactly ~w km exists.  ~w km is optimal.~n", [Cl, Cl])
      ;  format("~nNOT VERIFIED.~n"), fail ).
