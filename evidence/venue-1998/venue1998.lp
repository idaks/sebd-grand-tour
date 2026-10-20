% venue1998.lp -- where was SEBD 1998 held?  An unresolved fact, as rules.
%
% Run (clingo 5.x):
%   clingo venue1998.lp -n 0                          all readings (stable models)
%   clingo venue1998.lp -n 0 --enum-mode=cautious     true in EVERY reading (skeptical)
%   clingo venue1998.lp -n 0 --enum-mode=brave        true in SOME reading (credulous)
%
% Three kinds of statement, kept apart on purpose:
%   KNOWN       strict facts: what each source says, how sources relate, geography;
%   ASSUMED     an explicit choice the evidence does not settle (here: what the label
%               "Ancona" refers to); every reading states which assumption it makes;
%   DEFEASIBLE  "a reliable source saying X supports X, unless something defeats it",
%               written with default negation (not).
% Undercutters attack a source's reliability, not its conclusion.
%
% Revised 2026-10-20: the first version stated as a KNOWN fact that "Ancona" names
% the comune, and at the same time let that label support "the city proper".  That
% hid an assumption inside the rules; a review note caught it before publication.
% The label's referent is now an explicit ASSUMED choice with both options open.
% Written 2026-10-20 by Claude Code (Opus 5.5) with Bertram Ludäscher.

% ------------------------------------------------------------ strict: the sources
% s(Id, Kind, Claim): source Id, of Kind, says Claim.
s(history,  eyewitness, venue(portonovo)).       % sebd.inf.uniroma3.it/history.html:
                                                 % "Nel 1998 siamo tornati al mare, a
                                                 %  Portonovo ... vicino ad Ancona"
s(title,    label,      place(ancona)).          % proceedings title (via DBLP):
                                                 % "SEBD 1998, Ancona, Italy, 23-25 Giugno"
s(events,   label,      place(ancona)).          % sebd.inf.uniroma3.it/index.html#events:
                                                 % "6th SEBD - June 23-25, 1998, Ancona, Marche"
s(gemini,   inference,  venue(campus)).          % Gemini, 2026-10-20: "highly likely ...
                                                 % the university's engineering campus"

copies(events, title).       % the events list links each edition to DBLP: same witness
unsourced(gemini).           % a plausibility argument, no source cited

% ------------------------------------------------------------ strict: geography
in(portonovo, ancona_municipality).   % Portonovo is a frazione of the comune of Ancona
in(campus,    ancona_city).
in(ancona_city, ancona_municipality).

% ------------------------------------------------------------ assumed: the label
% "Ancona" on a title page may name the city where the meeting was held (a common
% convention), or only the comune / area, which includes Portonovo.  Nothing we have
% decides which, so each reading picks one, and says so.
1 { label_means(city) ; label_means(municipality) } 1.

% ------------------------------------------------------------ undercutters
% A source that only repeats another, or cites nothing, is not an independent witness.
undercut(S) :- copies(S, _).
undercut(S) :- unsourced(S).
witness(S) :- s(S, _, _), not undercut(S).

% ------------------------------------------------------------ defeasible rules
% The two venue readings exclude each other; each holds unless the other does.
venue(portonovo)   :- s(S, eyewitness, venue(portonovo)), witness(S), not venue(ancona_city).
venue(ancona_city) :- s(S, label, place(ancona)), witness(S), label_means(city),
                      not venue(portonovo).
venue(ancona_city) :- s(S, _, venue(campus)), witness(S), not venue(portonovo).

% ------------------------------------------------------------ strict consequences
% Coarser claims follow strictly from finer ones, and from the label itself.
at(X) :- venue(X).
at(Y) :- at(X), in(X, Y).
% Either referent of the label lies within the comune, so this is KNOWN, not assumed.
at(ancona_municipality) :- s(S, label, place(ancona)), witness(S).

% ------------------------------------------------------------ optional evidence
% Uncomment ONE to see how new evidence would close the question:
% organizer_says(portonovo).       % a 1998 organizer confirms Portonovo
% organizer_says(ancona_city).     % ... or confirms the city
% :- label_means(city).            % fix the assumption: the label names only the comune
% :- label_means(municipality).    % fix the assumption: the label names the city proper
#defined organizer_says/1.
:- organizer_says(X), not venue(X).
venue(ancona_city) :- organizer_says(ancona_city).
venue(portonovo)   :- organizer_says(portonovo).

#show label_means/1.
#show venue/1.
#show at/1.
#show witness/1.
#show undercut/1.
