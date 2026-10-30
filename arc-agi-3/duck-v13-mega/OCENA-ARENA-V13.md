# OCENA ARENA — v13-MEGA (Pokemon 3782f8c; weryfikacja niezależna 30.10 ~07:15 UTC)
Wszystko poniżej robiłem SAM na czystych artefaktach (nie ufam deklaracjom — sprawdzam).

## Wyniki niezależnej weryfikacji
1. **Patch chain 6/6 na CZYSTYM bundlu r033** (git archive z HEAD; extract z notebooka ich ekstraktorem):
   harness-changes + extra-00..04 aplikują się czysto, spatchowane drzewo się kompiluje, moduł
   `inference/framework/arc3_winpath.py` obecny; standalone `src/arc3_winpath.py` == spatchowany (byte-identical).
2. **Testy: plan-commit 12/12 OK, winpath 6/6 OK** (wcześniejsze błędy = braki piaskownicy: PIL, arcengine na sys.path —
   po doinstalowaniu/dodaniu PYTHONPATH wszystko zielone).
3. **PLAYBOOK 14/14 POTWIERDZONY PRZEZ MNIE NA PRAWDZIWYM SILNIKU** (arcengine 0.9.3 / arc-agi 0.9.9 + kody gier z repo):
   sekwencje z playbook.json (9 gier: cd82, cn04, ft09, lp85, ls20, m0r0×2, sp80, tu93×4, vc33×2) zdejmą poziomy
   deterministycznie — replay od startu gry przez kolejne poziomy przeszedł w całości (skrypt replay_pb w SYNC §13).
4. **Struktura rosteru POTWIERDZONA W KODZIE FRAMEWORKU** (nie hipoteza!): `make_benchmark_kaggle_official_110`:
   "The 25 official games are **repeated round-robin to 110** independent GameAPI entries" (n_passes=1/entry,
   klony `k…` = ten sam base env pod spodem). Czyli: klonów ~4.4/gra i playbook gra na każdym klonie.
5. metadata id=title=arc3-duck-v13-mega; /kaggle/input zadeklarowane; przełączniki PLAN_COMMIT i kill-switche obecne w obie strony.

## Uwagi krytyczne (nie blokujące)
- Multi-zmiana na jeden slot (commit ON + cap OFF + winpath + dead-skip) = atrybucja rozmyta; kill-switche to łagodzą,
  a przy 4 slotach i progu 49.85 SUFIT jest ważniejszy niż czystość atrybucji.
- ANALIZA-23 (rozcienienie tokenów na pełnym rosterze; smoke≠predyktor LB) jest spójna z naszymi danymi
  (v3: smoke 29.02 -> LB 26.25; v11: smoke 18.55 -> 23.89) — bramka smoke zostaje jako wykrywacz katastrof, nie estymator.
- "20 passów" w ANALIZA-23 ≠ kod frameworka (110 wpisów, round-robin; ~4.4/gra). Mnożnik replay jest więc ~4.4×, nie 20×.
- Patch 0006 liczy replay-akcje normalnie (nie oszukuje RHAE) — oszczędność = tokeny + kara kwadratowa za re-eksplorację.

## Wniosek dla slotów (rewizja GO z §12)
**GO#1 NOWY: v13-MEGA na slot 30.10** (jedyny kandydat z dźwignią o suficie 45-55; playbook zweryfikowany 14/14 na silniku;
konczenci: commit=ON, cap=OFF, replay, dead-skip, fix conc=10). v12 (c45+fix) = FALLBACK na 31.10, gdyby smoke v13
wykazał katastrofe (kill-switche kolejno). PC sweep (600 s, 5950X) przed submitem powiekszy playbook (kazdy poziom = zysk).
Wysylka = wyłacznie po GO usera.
