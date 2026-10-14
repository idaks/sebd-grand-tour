%% route_optimized(Step, From, To, Km).  Path-TSP 1->...->34.
%% Visiting order (Pos = position in trip, No = edition number):
visit( 1,  1).   %% Gizzeria Lido
visit( 2, 29).   %% Pizzo Calabro
visit( 3, 21).   %% Roccella Ionica
visit( 4, 25).   %% Squillace Lido
visit( 5, 24).   %% Ugento
visit( 6, 15).   %% Torre Canne
visit( 7, 26).   %% Castellaneta Marina
visit( 8, 19).   %% Maratea
visit( 9, 11).   %% Cetraro
visit(10, 16).   %% Mondello
visit(11, 12).   %% Santa Margherita di Pula
visit(12, 32).   %% Villasimius
visit(13, 28).   %% Villasimius
visit(14, 33).   %% Ischia
visit(15, 22).   %% Sorrento
visit(16,  3).   %% Ravello
visit(17, 23).   %% Gaeta
visit(18,  8).   %% L'Aquila
visit(19, 27).   %% Castiglione della Pescaia
visit(20, 10).   %% Portoferraio
visit(21,  4).   %% San Miniato
visit(22, 30).   %% Tirrenia
visit(23, 17).   %% Camogli
visit(24,  7).   %% Como
visit(25, 13).   %% Bressanone
visit(26,  5).   %% Verona
visit(27, 31).   %% Galzignano Terme
visit(28,  9).   %% Venice
visit(29, 20).   %% Venice
visit(30,  2).   %% Rimini
visit(31, 18).   %% Rimini
visit(32,  6).   %% Ancona
visit(33, 14).   %% Portonovo
visit(34, 34).   %% Senigallia

route_optimized( 1,  1, 29,   23).
route_optimized( 2, 29, 21,   50).
route_optimized( 3, 21, 25,   53).
route_optimized( 4, 25, 24,  183).
route_optimized( 5, 24, 15,  116).
route_optimized( 6, 15, 26,   60).
route_optimized( 7, 26, 19,  114).
route_optimized( 8, 19, 11,   55).
route_optimized( 9, 11, 16,  262).
route_optimized(10, 16, 12,  369).
route_optimized(11, 12, 32,   50).
route_optimized(12, 32, 28,    0).
route_optimized(13, 28, 33,  407).
route_optimized(14, 33, 22,   36).
route_optimized(15, 22,  3,   20).
route_optimized(16,  3, 23,  106).
route_optimized(17, 23,  8,  128).
route_optimized(18,  8, 27,  213).
route_optimized(19, 27, 10,   47).
route_optimized(20, 10,  4,  106).
route_optimized(21,  4, 30,   47).
route_optimized(22, 30, 17,  123).
route_optimized(23, 17,  7,  162).
route_optimized(24,  7, 13,  236).
route_optimized(25, 13,  5,  153).
route_optimized(26,  5, 31,   62).
route_optimized(27, 31,  9,   54).
route_optimized(28,  9, 20,    0).
route_optimized(29, 20,  2,  155).
route_optimized(30,  2, 18,    0).
route_optimized(31, 18,  6,   93).
route_optimized(32,  6, 14,    9).
route_optimized(33, 14, 34,   35).

total_optimized(3527).
