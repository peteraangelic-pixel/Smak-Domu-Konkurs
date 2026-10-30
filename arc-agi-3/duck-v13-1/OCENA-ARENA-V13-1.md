# OCENA ARENA — v13.1 (Pokemon cbefdd4; niezależna weryfikacja 30.10 ~07:30 UTC)
v13.1 = v13 + korekty po 3 recenzjach (Gemma/c87/Smak). Zweryfikowane SAM (czyste artefakty, nie deklaracje).

## Wyniki
1. **Diff v13 -> v13.1 chirurgiczny**: playbook.json IDENTYCZNY (moja walidacja 14/14 na silniku dalej obowiązuje!),
   notebook: tylko komórki 2 (przełączniki/env) i 11 (wiring base_key/DEAD_MIN_PASSES/WINPATH_DIR); metadata
   id=title=arc3-duck-v13-1 (title==slug OK), źródła c45-proven.
2. **Patch chain 6/6 na CZYSTYM bundlu r033** + drzewo się kompiluje; standalone src/arc3_winpath.py ==
   spatchowany moduł (bajt-identycznie).
3. **Testy: plan-commit 12/12 OK, winpath 7/7 OK** (pad u nich i u mnie w verify = brak arcengine/PIL w środowisku
   verify; na ręcznym biegu z PYTHONPATH wszystko zielone). Uwaga: komit mówi „12+8", w pliku jest 7 testów winpath —
   drobna niespójność opisu, nie kodu.
4. **base_key PRZEJRZANY**: 'ls20-9607627b' -> 'ls20' (fallback: sanitize pełnego id). Magazyn winpath WSPÓLNY dla
   wszystkich wpisów rosteru tej samej gry (~4.4 klony) — mnożnik replay zrobiony właściwie (poziom rozwiązany raz =
   replay w każdym kolejnym klonie za ~0 tokenów).
5. **dead-skip na licznikach magazynu** (ARC3_DEAD_MIN_PASSES=3): poprzednio klucz pass_index był martwy przy
   n_passes=1 (nasza korekta z §13 — przyjęta i naprawiona). Uczciwe NOTE w module: kanały replay = playbook offline,
   powtórzone wpisy (klony), powroty do ukończonego poziomu w ramach wpisu.

## Werdykt
**GO#1 na slot 30.10: v13.1 (duck-v13-1) — ZASTĘPUJE v13-mega** (te same dźwignie, poprawiony mnożnik pamięci
między klonami, działający dead-skip). Fallback bez zmian: v12 (31.10). Kill-switche: PLAN_COMMIT=0 / ARC3_WINPATH=0 /
ARC3_DEAD_SKIP=0 / (opc.) cap z powrotem 45000. Wysyłka = PO GO usera.
Log kontrolny po pushu: `v13 profile=plan plan_commit=1`, `v13 playbook: 9 gier, 14 poziomów`, `level_token_cap=0`.
