%% verify.pl -- independent certificate checker for the optimized route.
%% Run:  swipl -q -g run -t halt verify.pl
%% It does NOT trust total_optimized/1: it recomputes the length from distance/3
%% and checks the route is a valid permutation 1..34 starting at 1, ending at 34.
%%
%% Hardened 2026-10-16 after an independent review (OpenAI Codex): the original
%% summed the stored legs route_optimized/4 without checking that they follow the
%% visiting order visit/2, so a reordered visit/2 still passed.  The length is now
%% computed from consecutive visits, and every stored leg must be exactly the leg
%% between two consecutive visits.  Original: original-2026-08-01/verify.pl.
:- [distance], [route_optimized].

tour_len([_], 0).
tour_len([A, B|T], L) :- dist(A, B, K), tour_len([B|T], R), L is R + K.

legs([_], []).
legs([A, B|T], [A-B|R]) :- legs([B|T], R).

run :-
    findall(P-No, visit(P, No), Ps),
    keysort(Ps, Sorted), pairs_keys_values(Sorted, Pos, Seq),
    length(Seq, N), numlist(1, N, Pos),
    ( Seq = [1|_], last(Seq, 34) -> true ; format("FAIL: endpoints~n"), fail ),
    ( msort(Seq, S), numlist(1, 34, S) -> true                 % permutation of 1..34
    ; format("FAIL: not a permutation of 1..34~n"), fail ),
    tour_len(Seq, Recomputed),
    legs(Seq, Legs),
    findall(St-(A-B)-K, route_optimized(St, A, B, K), Stored0), msort(Stored0, Stored),
    length(Legs, NL), numlist(1, NL, Steps),
    ( findall(St-L-K, (nth1(St, Legs, L), L = X-Y, dist(X, Y, K)), Stored),
      length(Steps, NL)
      -> true
      ;  format("FAIL: stored legs do not match the consecutive visits~n"), fail ),
    total_optimized(Published),
    ( Recomputed =:= Published
        -> format("PASS: valid 1..34 permutation; recomputed = published = ~w km~n",
                  [Recomputed])
        ;  format("FAIL: recomputed ~w =/= published ~w~n", [Recomputed, Published]), fail ).
