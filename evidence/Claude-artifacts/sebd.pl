% sebd.pl  --  SEBD conference editions (1993-2026) with approximate coordinates.
% Schema:  sebd(Number, Year, City, Lat, Long).
%   Lat = degrees North, Long = degrees East (decimal degrees).
%   Coordinates are approximate town centroids (~+/-2 km). All locations are in Italy.
%   Verified against OpenStreetMap/Nominatim 2026-08-01; editions 1, 15, 25, 26 were
%   corrected then (each had drifted inland from its coastal frazione to the parent comune).
% Load:  swipl sebd.pl     Query:  ?- sebd_repeat(City, Years).

sebd( 1, 1993, 'Gizzeria Lido',             38.93, 16.22).
sebd( 2, 1994, 'Rimini',                    44.06, 12.57).
sebd( 3, 1995, 'Ravello',                   40.65, 14.61).
sebd( 4, 1996, 'San Miniato',               43.68, 10.85).
sebd( 5, 1997, 'Verona',                    45.44, 10.99).
sebd( 6, 1998, 'Ancona',                    43.62, 13.52).
sebd( 7, 1999, 'Como',                      45.81,  9.08).
sebd( 8, 2000, 'L\'Aquila',                 42.35, 13.40).
sebd( 9, 2001, 'Venice',                    45.44, 12.34).
sebd(10, 2002, 'Portoferraio',              42.81, 10.32).
sebd(11, 2003, 'Cetraro',                   39.52, 15.94).
sebd(12, 2004, 'Santa Margherita di Pula',  38.96,  8.97).
sebd(13, 2005, 'Bressanone',                46.72, 11.66).
sebd(14, 2006, 'Portonovo',                 43.56, 13.59).
sebd(15, 2007, 'Torre Canne',               40.84, 17.47).
sebd(16, 2008, 'Mondello',                  38.20, 13.32).
sebd(17, 2009, 'Camogli',                   44.35,  9.16).
sebd(18, 2010, 'Rimini',                    44.06, 12.57).
sebd(19, 2011, 'Maratea',                   39.99, 15.72).
sebd(20, 2012, 'Venice',                    45.44, 12.34).
sebd(21, 2013, 'Roccella Ionica',           38.32, 16.40).
sebd(22, 2014, 'Sorrento',                  40.63, 14.37).
sebd(23, 2015, 'Gaeta',                     41.21, 13.57).
sebd(24, 2016, 'Ugento',                    39.93, 18.16).
sebd(25, 2017, 'Squillace Lido',            38.78, 16.57).
sebd(26, 2018, 'Castellaneta Marina',       40.47, 16.94).
sebd(27, 2019, 'Castiglione della Pescaia', 42.76, 10.88).
sebd(28, 2020, 'Villasimius',               39.14,  9.52).
sebd(29, 2021, 'Pizzo Calabro',             38.73, 16.16).
sebd(30, 2022, 'Tirrenia',                  43.63, 10.29).
sebd(31, 2023, 'Galzignano Terme',          45.30, 11.72).
sebd(32, 2024, 'Villasimius',               39.14,  9.52).
sebd(33, 2025, 'Ischia',                    40.73, 13.95).
sebd(34, 2026, 'Senigallia',                43.71, 13.22).

% --- Views -----------------------------------------------------------------

% sebd_repeat(City): a city that has hosted two or more editions.
sebd_repeat(City) :-
    setof(Year, N^Lat^Long^sebd(N, Year, City, Lat, Long), Years),
    Years = [_, _|_].                       % at least two distinct years

% sebd_repeat(City, Years): same, but also returns the sorted list of host years.
sebd_repeat(City, Years) :-
    setof(Year, N^Lat^Long^sebd(N, Year, City, Lat, Long), Years),
    Years = [_, _|_].

% Example queries:
%   ?- sebd_repeat(City).               % -> Rimini ; Venice ; Villasimius
%   ?- sebd_repeat(City, Years).        % -> 'Rimini', [1994,2010] ; ...
%   ?- aggregate_all(count, sebd(_,_,_,_,_), N).   % -> N = 34
