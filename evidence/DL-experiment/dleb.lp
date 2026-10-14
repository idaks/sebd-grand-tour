% Listing 1 (basic) + Listings 7+8 (DL encoding with Exit Bound, DLEB)
% from Bertagnon & Gavanelli, JLC 36(2) 2026, doi:10.1093/logcom/exaf072
{ cycle(A,B): cost(A,B,_) }=1 :- point(A,_,_).
{ cycle(A,B): cost(A,B,_) }=1 :- point(B,_,_).
:- point(B,_,_), not reached(B).
firstpoint(X) :- X = #min{ Y: point(Y,_,_) }.
reached(X) :- firstpoint(X).
reached(B) :- cycle(A,B), reached(A).
&diff{total(X-1)-0} <= 0 :- firstpoint(X).
&diff{0-total(X-1)} <= 0 :- firstpoint(X).
lastpoint(X) :- X = #max{ Y: point(Y,_,_) }.
&diff{total(N-1)-total(N)} <= -C :- point(N,_,_), cycle(N,B), cost(N,B,C).
&diff{total(N)-totalcost} <= 0 :- lastpoint(N).
&diff{total(N-1)-total(N)} <= -C :- point(N,_,_), mincost_exit_node(N,C).
mincost_exit_node(N,C) :- point(N,_,_), C = #min{ Cost: cost(N,B,Cost), point(B,_,_), B!=N }.
#show cycle/2.
