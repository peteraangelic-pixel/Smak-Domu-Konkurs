# ANALIZA SMOKE c45 (r076) -> decyzja slotu 26.10
- smoke 10x48min: MEAN 26.78 (v3=29.02, v6=27.21); rerun 2.2h/gra = wiecej glebokosci; LB c45 ~21:30 = prawdziwy pomiar.
- ZYSKI (cap dziala): cn04 71.4 (47.6), m0r0 46.3 (28.6), ka59 49.9 (17.9), ls20 8.8 (3.3).
- STRATY (cap tnie dlugie poziomy): su15 13.3 (56.4!), sc25 17.1 (42.6), dc22 27.7 (44.8).
- tok/act 828 (=841); a/call 4.73 (batching nie ruszony).
- DECYZJA 26.10 (po LB c45 ~21:30): LB c45 >= 29 -> v9 profil c45-faithful; LB < 29 -> v9 profil c45 z ARC3_LEVEL_TOKEN_CAP=0 (usuwa podejrzanego regresu su15/sc25). deep/wide -> 27.10+.
