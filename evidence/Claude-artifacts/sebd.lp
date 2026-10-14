% sebd.lp  --  SEBD conference editions (1993-2026) in clingo/ASP.
%
% Schema:  sebd(Number, Year, City, Lat, Long).
%   clingo terms are INTEGERS (no floats), so Lat/Long are stored in
%   CENTIDEGREES = decimal degrees x 100.  e.g. 3897 = 38.97 N, 1617 = 16.17 E.
%   All locations are in Italy; coords are approximate town centroids.
%
% Run:   clingo sebd.lp
%        clingo sebd.lp 0        % (all answer sets; here there is exactly one)

sebd( 1, 1993, "Gizzeria Lido",             3893, 1622).
sebd( 2, 1994, "Rimini",                    4406, 1257).
sebd( 3, 1995, "Ravello",                   4065, 1461).
sebd( 4, 1996, "San Miniato",               4368, 1085).
sebd( 5, 1997, "Verona",                    4544, 1099).
sebd( 6, 1998, "Ancona",                    4362, 1352).
sebd( 7, 1999, "Como",                      4581,  908).
sebd( 8, 2000, "L'Aquila",                  4235, 1340).
sebd( 9, 2001, "Venice",                    4544, 1234).
sebd(10, 2002, "Portoferraio",              4281, 1032).
sebd(11, 2003, "Cetraro",                   3952, 1594).
sebd(12, 2004, "Santa Margherita di Pula",  3896,  897).
sebd(13, 2005, "Bressanone",                4672, 1166).
sebd(14, 2006, "Portonovo",                 4356, 1359).
sebd(15, 2007, "Torre Canne",               4084, 1747).
sebd(16, 2008, "Mondello",                  3820, 1332).
sebd(17, 2009, "Camogli",                   4435,  916).
sebd(18, 2010, "Rimini",                    4406, 1257).
sebd(19, 2011, "Maratea",                   3999, 1572).
sebd(20, 2012, "Venice",                    4544, 1234).
sebd(21, 2013, "Roccella Ionica",           3832, 1640).
sebd(22, 2014, "Sorrento",                  4063, 1437).
sebd(23, 2015, "Gaeta",                     4121, 1357).
sebd(24, 2016, "Ugento",                    3993, 1816).
sebd(25, 2017, "Squillace Lido",            3878, 1657).
sebd(26, 2018, "Castellaneta Marina",       4047, 1694).
sebd(27, 2019, "Castiglione della Pescaia", 4276, 1088).
sebd(28, 2020, "Villasimius",               3914,  952).
sebd(29, 2021, "Pizzo Calabro",             3873, 1616).
sebd(30, 2022, "Tirrenia",                  4363, 1029).
sebd(31, 2023, "Galzignano Terme",          4530, 1172).
sebd(32, 2024, "Villasimius",               3914,  952).
sebd(33, 2025, "Ischia",                    4073, 1395).
sebd(34, 2026, "Senigallia",                4371, 1322).

% --- Views -----------------------------------------------------------------

% Every host city.
city(C) :- sebd(_, _, C, _, _).

% sebd_repeat(C): a city that has hosted two or more editions.
% (aggregate form: count the distinct host years for the city)
sebd_repeat(C) :- city(C), #count { Y : sebd(_, Y, C, _, _) } >= 2.

%   Equivalent join form (kept as a comment for the talk):
%   sebd_repeat(C) :- sebd(_, Y1, C, _, _), sebd(_, Y2, C, _, _), Y1 < Y2.

% sebd_repeat_year(C, Y): the (city, year) pairs for repeat hosts
% (relational analog of Prolog's sebd_repeat(City, Years) list).
sebd_repeat_year(C, Y) :- sebd_repeat(C), sebd(_, Y, C, _, _).

% Show only the views (suppress the 34 base facts in the answer set).
#show sebd_repeat/1.
#show sebd_repeat_year/2.
