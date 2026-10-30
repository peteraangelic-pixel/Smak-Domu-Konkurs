# OCENA ARENA — duck-v13.5-consensus („round 08:00–08:12" włączona, 30.10 2026 ~11:15 UTC)

**Werdykt: CERTYFIKOWANA — ALL CHECKS PASSED (39 komórek, 8/8 patchy czysty r033,
12 plan-commit + 6 escalate-relative + 11 winpath na spatchowanym drzewie, sondy na
stubach z nowymi testami baseline/coverage, playbook bajtowo identyczny, serving
nietknięty). Kandydat na slot 30.10. NIC do Kaggle bez wyraźnego GO usera.**

v13.5 = v13.4-unified + wszystko, co wniosła fala komitów 08:00–08:12 na 4 gałęziach.

## 1. Co przyszło w fali 08:00–08:12 (przeczytane w całości, zweryfikowane)

| gałąź | commit(y) | treść | werdykt Areny |
|---|---|---|---|
| 7911 | 1541d08 | **KOREKTA centralnej liczby**: „1,00 akcji/decyzję" było artefaktem metody (wallclock rośnie przy każdej akcji); prawda: **4,61 akcji/generację, 853 tok/akcję**. Właściwy model budżetu: **model ogranicza DEKODOWANIE** (~186 tys. tok/grę @15,8 ms/tok → ~218 akcji/grę). Dźwignia = **mniej tok/akcję** (do 50: ~479 tok/akcję = −44%) | przyjmujemy; UWAGA: batching (hint) to właśnie mechanizm cięcia tok/akcję (mniej tur → mniej tokenów na akcję) — zgodne z audytem Gemmy naszego v13.3 |
| 7911 | 724189b | **Poprawiona reguła punktacji (30/30 na zapisanych wynikach): score = min(raw, cap) ≤ 100×pokrycie**. Do 50 potrzeba pokrycia 50% = **+1,1 poziomu/grę = +22% budżetu (206→253 akcji)**; 72 akcje/grę i tak idą w nieukończone próby; na ukończonych poziomach jesteśmy 1,7× szybsi od człowieka (pod sufitem 115, wiąże cap ukończenia). Przyjmuje ESCALATE=20 (zmiana z 10); prognoza „+1 poziom/grę" | przyjmujemy → **sonda rosteru loguje teraz pokrycie wazone** (wprost: sufit wyniku) |
| 7911 | c170f55 | **Pytanie o baseline DOMKNIĘTE NEGATYWNIE**: a450 duck-v15 sprawdził na r033 — **w submisji silnik UKRYWA baseline'y** (`base_actions_per_level is None`) → próg względny degeneruje do absolutnej 20 + cap 2; „czy wypełnione w rerunie = sonda, nie założenie" | przyjmujemy → **sonda rosteru mierzy widoczność baseline'u w prawdziwym rerunie**; nasz patch 0008 degraduje bezpiecznie (zaprojektowany fallback) |
| a450 | 8d96c68 | **duck-v15** = v14 Gemmy + ICH patch progu względnego (`pc_escalate_at()` w plan_commit utils, `ToolAgent(base_actions_per_level=...)` z konstruktora) — 7/7 patchy, 12+8+7 testów; sami potwierdzają degradację w submisji | równoległa implementacja tego samego pomysłu co nasz 0008; nasza wersja ma test odtwarzający 8/0 na r085 przez spatchowany kod; oba degenerują tak samo |
| Gemma | 07bf05e | **Audyt naszego v13.3-arena: PRZECHODZI** („mechanizm prawdziwy i lepszy kierunkowo od wszystkiego w v13.2"; „ta sama dźwignia co commit(plan), ale tańsza — batch nie zmienia liczby akcji, zmienia tok/akcję; a/call 4,36→6,5 ⇒ tok/akcję −33% ⇒ akcje/grę +50%"). Trzy zastrzeżenia → patrz niżej. **duck-v15 Gemmy** = nasze v13.3 + ESCALATE 20 + sondy z v14 (37 komórek) | baza v15 Gemmy = nasz pakiet — potwierdzenie kierunku; nasza v13.5 jest nadzbiorem (dodatkowo: log replayu, próg względny z capem, degradacja udokumentowana) |
| c87 | 980deff | 9. korekta (na korzyść dźwigni): domyka własną lukę (ESCALATE **jest** env — potwierdzone z komórki 2), PLAN_COMMIT=1 + ESCALATE=10 = spójna konfiguracja testu; lekcja: **„testy 6/6 zielone przy martwej funkcji"** | lekcja kluczowa dla nas → patrz §3 (uczciwość o degradacji 0008) |

## 2. Zastrzeżenie Gemmy o historii — ODRZUCAME z dowodem

Gemma (audyt v13.3 §2c): „trim historii 150→48 jest odwrócony, bo domyślna wartość to 30". To
prawda o DOMYŚLNEJ, ale **nasz notebook wprost pinuje `ARC3_HISTORY_ASSISTANT_TURNS: 150` w
setup_env (komórka 15)** — pipnięcie potwierdzone w zbudowanym notebooku; to samo wiedziała
gałąź 6d081d52 („efektywny 150, nie domyślne 30"). Nasz opis opcji (150→48 = trim) jest więc
POPRAWNY dla naszego pakietu. (Równolegle: jej MEGA-CONFIG **nadal** ma błędną etykietę r110
„8B cap 45k" — nasza korekta §17D pozostaje jedyną zweryfikowaną.) Sama OPCJA trimu zostaje
niezmierzona i NIE wchodzi do v13.5 (konsensus: sonda najpierw, decyzja potem).

## 3. Co zmienia v13.5 względem v13.4 (cell-diff: 1, 2, 12, 31, 38)

1. **Komórka 2 — konsensus spisany w kodzie**: degradacja progu względnego w submisji
   (silnik ukrywa baseline'y), realne zachowanie rerunu = **absolutna 20 + cap 2 = 42
   wstrzyknięcia na r085 (2,9% puli; @10 było 154/15,3%)**; napięcie Gemma(20) vs 7911(30–60)
   → cap 2 ogranicza oba; wartość `escalate=` logowana → weryfikowalna z logu rerunu.
   Print: `v13.5-consensus profile=…`.
2. **Sonda rosteru (kom. 38) rozszerzona** (read-only, po biegu):
   - per-run: `baseline` (hidden/present/brak-atrybutu) + `coverage_pct` (pokrycie wazone
     wagami k=k+1: score ≤ 100×pokrycie — reguła 30/30 z 724189b);
   - summary + werdykty: „srednie wazone pokrycie X% -> sufit wyniku ~X pkt" oraz
     „baseline UKRYTY w submisji -> prog wzgledny nieaktywny" / „baseline widoczny w N
     runach -> prog wzgledny ZYWY".
3. Rebrandy (nazwa wariantu `v13-5-consensus`, metadata, writer 0007, sondy v13.5).

Patch chain BEZ ZMIAN (0001–0008; ten sam 0008 co w v13.4). Kill-switcze bez zmian
(RELATIVE=0 → v14-exact; OPENER=0 → v14; WINPATH_LOG=0; WINPATH/DEAD_SKIP/PLAN_COMMIT/CAP).

## 4. Weryfikacja (samodzielna, 30.10 ~11:15)

- `tools/verify_v13.py --bundle r033 --tests` → **ALL CHECKS PASSED** (nowe checki:
  „degradation documented in switch cell", „baseline visibility + coverage logged").
- 12 plan-commit + 6 escalate-relative (w tym odtworzenie 8 nudge'ów/0 przedwczesnych na
  prawdziwym r085 przez spatchowany `_escalate_threshold`) + 11 winpath na spatchowanym drzewie.
- Sondy na stubach: budżet (11,04×), roster (duplikaty, werdykt 0 pkt, alarm a/call,
  **pokrycie 19,8% → sufit ~20 pkt**, **baseline widoczny/UKRYTY werdykt**), wyjątek-proof, guard hooka.
- Playbook bajtowo v13.2/v13.3/v13.4 (14/14 na silniku — przejmowane); serving kom. 22 == stara 21.
- Pułapka środowiskowa ZNALEZIONA I USUNIĘTA podczas weryfikacji: nieudany `tar
  --strip-components=2` zostawił **/tmp/src/arc3_winpath.py** (stary moduł bez `_log`), który
  przez `sys.path.insert(0, parent.parent/src)` w testach ZACIENIAŁ moduł z drzewa →
  „zielone testy na martwym module" — dokładnie lekcja c87 (980deff) w praktyce. /tmp/src usunięte;
  testy po oczyszczeniu: 11/11.

## 5. Mapa pakietów „v15" u kolegów i nasza pozycja

| pakiet | baza | hint | log replayu | ESCALATE | względny próg | sondy | pokrycie/baseline probe |
|---|---|---|---|---|---|---|---|
| a450 duck-v15 (8d96c68) | v14 Gemmy | – | – | 20 | TAK (degeneruje) | tak | – |
| Gemma duck-v15 (07bf05e) | **nasze v13.3** | TAK | TAK (0007) | 20 | – | tak | – |
| **nasze v13.5-consensus** | v13.4 | **TAK** | **TAK** | **20 (+cap 2 = 42 zmierzone)** | **TAK (degeneruje, udokumentowane)** | **tak** | **TAK (nowe)** |

## 6. Propozycja slotów (decyduje GO usera)

- **30.10: v13.5-consensus** — pełny nadzbiór wszystkich wersji kolegów + metryki 7911.
- 31.10: v13.5 ×2 (draw) lub kontrola wg preferencji (v14-exact: RELATIVE=0 + OPENER=0 w
  naszym pakiecie = bez osobnego kernela).
- 1.11: flip najsłabszego komponentu wg meteringu (kandydaci: RELATIVE=0; HISTORY 150→48 —
  opcja poprawnie opisana, niezmierzona; treść dyrektywy eskalacyjnej do skrócenia — postulat
  7911, wymaga patcha prompts.py → nie teraz).
- 2.11: select best.
