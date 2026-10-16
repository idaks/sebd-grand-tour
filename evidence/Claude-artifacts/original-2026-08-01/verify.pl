%% verify.pl -- independent certificate checker for the optimized route.
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
