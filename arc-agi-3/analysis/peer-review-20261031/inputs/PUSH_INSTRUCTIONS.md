# Jak wypchnąć paczkę — stan na 31.10.2026, 14:44 UTC

## Odpowiedź na „czy zakomitowałeś wszystko?"

**Nie. Nie mogę.** Ta sesja nie ma poświadczeń GitHuba — sprawdzone ponownie teraz:

```
$ env | grep -ciE 'token|github'   -> 0
$ ls ~/.netrc ~/.git-credentials   -> brak
$ cd arc3_review_branch && git status -> fatal: not a git repository
```

Katalog paczki **nie jest nawet repozytorium git** — to zwykłe pliki przygotowane do wgrania.
Wszystko, co robiłem w tej kampanii, lądowało w repo **ręcznie, przez `Add files via upload`**
(albo przez inną sesję, która miała token). To nie jest przeoczenie: to ograniczenie środowiska,
które zgłosiłem w pierwszej turze, w której o to pytałeś.

## Co jest gotowe (24 pliki, manifest z hashami w `MANIFEST.md`)

| katalog | zawartość |
|---|---|
| `ARC3/duck-v17-action-efficiency/` | warstwa + pomiar + ablacja + `KOREKTA-2026-10-30.md` |
| `ARC3/AUDYT-pakietu-20261031.md` | **najnowsze**: audyt pakietu 31.10 + diagnoza wyniku 13,28 |
| `ARC3/OCENA-raportu-przegladowego.md` | ocena raportu 6 gałęzi |
| `ARC3/WERYFIKACJA-opinii-7911.md` | weryfikacja opinii 7911 (jest już na Smaku jako `de67be4`) |
| `ARC3/REVIEWS/` | audyt gałęzi + stan konkursu |
| `AVX512/` | źródła i raport AVX-512 |

## Jedna komenda (w katalogu `arc3_review_branch/`)

```bash
git init -q && git checkout -q -b arena/ae-audit-20261031
git add -A
git -c user.name="arena-agent" \
    -c user.email="297053741+arena-agent@users.noreply.github.com" \
    commit -q -m "ARC3: audyt pakietu 31.10 + diagnoza wyniku 13,28 + warstwa AE (RHAE 4,72 -> 39,16)

Contribution by Arena.ai session (sandbox has no GitHub credentials).

DIAGNOZA 13,28 (najwazniejsze):
- cap byl WYLACZONY (ARC3_LEVEL_TOKEN_CAP=0 w ARC3_VARIANT, guard in (None,'') nie nadpisuje)
  -> caly spor o arming 20k jest dla tego wyniku bez znaczenia
- 13,28 odpowiada ~2,5 poziomu/gre (skala r085: 1 poz.=3,48; 1-2=9,26; 1-3=17,88)
- mechanizm: smoke 22,59 przy 48 min/gra na 10 grach vs submisja na rosterze ~110
  -> 11x mniej czasu na gre; patche kosztuja ~+16% tokenow (141,7k -> 186k tok/gra)
- wniosek: dopoki roster jest 11x wiekszy niz smoke, ZADEN smoke ni symulacja nie ranguje wariantow

AUDYT KODU (v18):
- template_transfer.py: czysty numpy, zero arcengine/game_id - POTWIERDZONE
- hook: kontroler dostaje tylko grid/controls/level; fallback do LLM poprawny
- pytest: 35 passed; public25: template 3 poziomy/25 akcji na 1 grze z 25 (+0,3 pkt na sredniej)
- BRAK pomiaru falszywych rozpoznan - ryzyko regresji przed uzyciem w submicie

NIEZWERYFIKOWANE na GPU i na gatewayu. Traktowac jako hipotezy."
git remote add origin https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs.git
git push -u origin arena/ae-audit-20261031
```

**Nazwa gałęzi `arena/ae-audit-20261031` — celowo inna niż `v17`.** Istnieją już cztery
znaczenia „v17" (7911, Gemma `v17-arena`, Gemma `v17-arena-dyn`, moja `duck-v17-action-efficiency`).
Nie dokładam piątego.

## Weryfikacja po wypchnięciu

```bash
git ls-remote origin "refs/heads/arena/ae-audit-20261031"   # ma być 1 SHA
git show --stat HEAD | head -30                             # 24 pliki
```

Hash plików sprawdzisz wobec `MANIFEST.md` w paczce.

## Czego w paczce NIE ma

* `arc3_lab/` (katalog roboczy z `sim.py`, `agent.py`, `co_next.py`, `realloc.py`) —
  **jest**, w `ARC3/duck-v17-action-efficiency/`. To te same pliki.
* Surowych benchmarków (`benchmark.json` z r085) — **nie kopiuję cudzych artefaktów do repo**;
  narzędzia (`co_next.py`, `realloc.py`) przyjmują ścieżkę jako argument.
* Nic na Kaggle: zero submisji, zero runów GPU, zero zmian w notebookach.
