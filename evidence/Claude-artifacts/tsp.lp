% tsp.lp -- path-TSP over the SEBD stops, in clingo/ASP.
% Find a shortest Hamiltonian PATH from stop `start` to stop `end` visiting all
% 34 stops, using the symmetric distance/3 facts.  A (weak) clingo cross-check of
% the route from trip.py; exact_tsp.py PROVES the optimum = 3541 km.
%
% Run (find + prove optimum, may take a while for 34 nodes):
%   clingo tsp.lp distance.lp --opt-mode=opt --time-limit=120 -t4
% Run (just confirm 3541 is achievable, fast):
%   clingo tsp.lp distance.lp --opt-mode=optN,3541 -q

#const start = 1.
#const end   = 34.

node(N) :- distance(N,_,_).
node(N) :- distance(_,N,_).

% Directed edges in both orientations (distance is symmetric, stored once).
edge(A,B,C) :- distance(A,B,C).
edge(B,A,C) :- distance(A,B,C).

% Exactly one successor for every node except the end.
{ succ(A,B) : edge(A,B,_) } = 1 :- node(A), A != end.
% Exactly one predecessor for every node except the start.
{ succ(A,B) : edge(A,B,_) } = 1 :- node(B), B != start.
% Start has no predecessor; end has no successor.
:- succ(_, start).
:- succ(end, _).

% Connectivity: every node reachable from the start along chosen edges.
reach(start).
reach(B) :- reach(A), succ(A,B).
:- node(N), not reach(N).

% Minimize total kilometres of the chosen path.
#minimize { C,A,B : succ(A,B), edge(A,B,C) }.

#show succ/2.
