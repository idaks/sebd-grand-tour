% Listing 1 (basic) + Listing 5 (simple DL) + Listing 6 (triangle-ineq speedup)
% from Bertagnon & Gavanelli, JLC 36(2) 2026, doi:10.1093/logcom/exaf072
{ cycle(A,B): cost(A,B,_) }=1 :- point(A,_,_).
{ cycle(A,B): cost(A,B,_) }=1 :- point(B,_,_).
:- point(B,_,_), not reached(B).
firstpoint(X) :- X = #min{ Y: point(Y,_,_) }.
reached(X) :- firstpoint(X).
reached(B) :- cycle(A,B), reached(A).
&diff{0-visit(X)} <= 0 :- point(X,_,_).
&diff{visit(X)-visit(Y)} <= -C :- cycle(X,Y), cost(X,Y,C), not firstpoint(Y).
&diff{visit(X)-totalcost} <= -C :- cycle(X,F), cost(X,F,C), firstpoint(F).
&diff{0-visit(X)} <= -C :- point(X,_,_), cost(F,X,C), firstpoint(F).
&diff{visit(X)-totalcost} <= -C :- point(X,_,_), cost(X,F,C), firstpoint(F).
#show cycle/2.
