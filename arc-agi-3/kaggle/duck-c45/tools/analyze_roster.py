#!/usr/bin/env python3
"""Czyta roster_probe.jsonl z runu i mowi, czy roster sie powtarza.

Pytanie, na ktore odpowiada: czy 110 runow to 25 gier x ~4.4 repliki?
Jesli tak, pamiec miedzy replikami jest mnoznikiem ~4.4 na effective budget
i tylko ona ma rozmiar, ktory zamyka luke 208 vs 685 akcji.

Uzycie:
    python3 candidate-45/tools/analyze_roster.py [roster_probe.jsonl]

Wynik: liczba runow, liczba roznych plansz startowych, histogram powtorzen,
i werdykt CYCLIC / DISTINCT / ZA MALO DANYCH.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

DEFAULT = Path("/kaggle/working/roster_probe.jsonl")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.is_file():
        print(f"brak pliku: {path}")
        return 2

    starts = []
    ends = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("event") == "start":
            starts.append(rec)
        elif rec.get("event") == "end":
            ends += 1

    if not starts:
        print("brak wpisow start - sonda nie zadzialala?")
        return 3

    by_hash: dict[str, list[dict]] = collections.defaultdict(list)
    by_game: dict[str, list[dict]] = collections.defaultdict(list)
    for rec in starts:
        by_hash[rec.get("frame0") or "brak-hashu"].append(rec)
        by_game[str(rec.get("game_id"))].append(rec)

    sizes = collections.Counter(len(v) for v in by_hash.values())
    total = len(starts)
    distinct = len(by_hash)
    max_rep = max(sizes) if sizes else 0

    print(f"plik            : {path}")
    print(f"runy (start)    : {total}")
    print(f"runy (end)      : {ends}")
    print(f"game_id unikalne: {len(by_game)}")
    print(f"plansze unikalne: {distinct}")
    print(f"powtorzen/plansz: {dict(sorted(sizes.items()))}")
    if distinct:
        print(f"srednia replik  : {total / distinct:.2f}")

    # Repliki tej samej planszy pod roznymi game_id => roster cykliczny.
    cross_id = [v for v in by_hash.values() if len({str(r.get('game_id')) for r in v}) > 1]
    same_id = [v for v in by_hash.values() if len(v) > 1 and len({str(r.get('game_id')) for r in v}) == 1]

    print()
    if distinct and total / distinct >= 2.5 and cross_id:
        print(f"WERDYKT: CYCLIC - {len(cross_id)} plansz wystapilo pod wieloma game_id.")
        print("  => pamiec miedzy replikami (scope po planszy/zrodle) jest mnoznikiem")
        print(f"     ~{total / distinct:.1f}x na effective budget. To najwieksza dzwignia.")
        return 0
    if same_id and not cross_id:
        print(f"WERDYKT: POWTORKI W RAMACH TEGO SAMEGO game_id ({len(same_id)}) - to pass'y, nie repliki.")
        print("  => roster raczej DISTINCT; mnoznika nie ma, zostaje MAXREQ i depth.")
        return 1
    if total < max(20, distinct):
        print("WERDYKT: ZA MALO DANYCH - za malo runow, zeby rozstrzygnac.")
        return 4
    print(f"WERDYKT: DISTINCT - {distinct} roznych plansz na {total} runow. Mnoznika nie ma.")
    print("  => zostaje MAXREQ (+45% puli) i depth na grach blisko progu.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())



                    game_id=getattr(self.game.game_run, "game_id", None),
                    index=self.game_index,
                    pass_index=self.pass_index,
                    levels=int(self.game.current_state.levels_completed),
                    actions=int(self.action_count),
                    frame_end=_frame_hash(self.game.current_state),
                )# === ARC3 candidate-45: hook do wklejenia NA KOŃCU cell 21 ==================
# (po ustawieniu bm.solver.* / bm.pass, przed "show config").
#
# Zasada: hook NIE MOZE zabic runu. Kazdy blok jest w try/except, a jedyny
# efekt uboczny to pliki w /kaggle/working.
#
# Co robi:
#   1. SONDA ROSTERU - loguje game_id + hash pierwszej i ostatniej ramki kazdego
#      runu. Jesli prywatny roster to 25 gier x ~4.4 repliki, ten sam hash
#      pojawi sie 4-5 razy i wiadomo, ze pamiec miedzy replikami placi.
#      Koszt: 0 dodatkowego GPU (jedzie z najblizszym prawdziwym submitem).
#   2. CAP PER POZIOM z 0004-standalone (0 = wylaczony). Domyslnie WLACZONY,
#      bo bez niego 35% tokenow idzie w poziom, ktory nigdy nie jest konczony.
#   3. Znacznik wersji w logu, zeby po fakcie nie zgadywac, co bieglo.

import hashlib as _c45_hash
import json as _c45_json
import os as _c45_os
import time as _c45_time
from pathlib import Path as _C45Path

C45 = {
    "id": "c45-candidate",
    "level_token_cap": int(_c45_os.environ.get("C45_LEVEL_TOKEN_CAP", "40000")),
    "probe": True,
}

# --- 2. cap per poziom ------------------------------------------------------
# ARC3_LEVEL_TOKEN_CAP=0 wylacza mechanizm (stare zachowanie).
_prev_cap = _c45_os.environ.get("ARC3_LEVEL_TOKEN_CAP")
if _prev_cap in (None, ""):
    _c45_os.environ["ARC3_LEVEL_TOKEN_CAP"] = str(C45["level_token_cap"])
_c45_os.environ.setdefault("ARC3_LEVEL_RESETS_MAX", "1")
print(f"ARC3 candidate-45: level_token_cap={_c45_os.environ['ARC3_LEVEL_TOKEN_CAP']} "
      f"(resets_max={_c45_os.environ['ARC3_LEVEL_RESETS_MAX']})", flush=True)


# --- 1. sonda rosteru -------------------------------------------------------
def _install_roster_probe():
    try:
        import numpy as _np
        import inference.framework.solver as _S
    except Exception as exc:  # brak numpy/solvera -> prob nie startuje
        return f"probe: POMINIETA ({exc!r})"

    out = _C45Path(_c45_os.environ.get("C45_PROBE_OUT", "/kaggle/working/roster_probe.jsonl"))

    def _frame_hash(state):
        try:
            grid = _S._grid_from_state(state)
            arr = _np.asarray(grid, dtype=_np.int16)
            return _c45_hash.blake2b(arr.tobytes(), digest_size=8).hexdigest()
        except Exception:
            return None

    def _emit(rec):
        try:
            with out.open("a", encoding="utf-8") as fh:
                fh.write(_c45_json.dumps(rec, sort_keys=True) + "\n")
        except Exception:
            pass

    _orig_play = _S._HarnessGameSession.play

    def play(self):  # noqa: ANN001 - metoda wstrzykiwana
        start = {"event": "start", "t": round(_c45_time.time(), 3)}
        try:
            state = self.game.current_state
            start.update(
                game_id=getattr(self.game.game_run, "game_id", None),
                index=self.game_index,
                pass_index=self.pass_index,
                frame0=_frame_hash(state),
                win_levels=getattr(state, "win_levels", None),
                actions_avail=list(getattr(state, "available_actions", []) or []),
            )
        except Exception as exc:
            start["error"] = repr(exc)
        _emit(start)
        try:
            return _orig_play(self)
        finally:
            end = {"event": "end", "t": round(_c45_time.time(), 3)}
            try:
                end.update(
            except Exception as exc:
                end["error"] = repr(exc)
            _emit(end)

    _S._HarnessGameSession.play = play
    return f"probe: OK -> {out}"


print(_install_roster_probe(), flush=True)
print("ARC3 candidate-45:", _c45_json.dumps(C45, sort_keys=True), flush=True)
# === koniec hooka candidate-45 =============================================


--- a/ops.py	2026-10-24 21:35:59.050520580 +0000
+++ b/ops.py	2026-10-24 21:35:59.074520580 +0000
@@ -134,12 +134,25 @@
     msg = str(args.get("message") or "duck @long200 (Smak-Domu-Konkurs arc3-ops)")
     ver = str(args.get("version") or "")
     file = str(args.get("file") or "submission.parquet")
+    # Kaggle CLI: `-f` to NAZWA pliku wyjsciowego kernela, nie sciezka.
+    # Sciezka konczy sie 400 CreateCodeSubmission, zanim cokolwiek innego
+    # zostanie sprawdzone (r048/r049: wersja COMPLETE, mimo to 400; 12 prob ze
+    # sciezka = 12x rc=1, 2 proby z nazwa = 2x rc=0). Normalizujemy tutaj,
+    # zamiast ufac wywolujacemu: to jedyne miejsce, ktore dotyka CLI.
+    note = ""
+    if "/" in file or chr(92) in file:
+        normalized = re.split(r"[/\\]", file)[-1]
+        note = (f"UWAGA: -f dostal sciezke {file!r}; CLI wymaga nazwy pliku "
+                f"wyjsciowego -> {normalized!r}\n")
+        file = normalized
+    if not file:
+        return note + "ODMOWA: -f pusty (nie podano nazwy pliku wyjsciowego)\n"
     cmd = ["competitions", "submit", "-c", COMP, "-k", kernel]
     if ver:
         cmd += ["-v", ver]
     cmd += ["-f", file, "-m", msg]
     code, out = kaggle(*cmd)
-    return f"## competitions submit {cmd}\nrc={code}\n{out}\n"
+    return note + f"## competitions submit {cmd}\nrc={code}\n{out}\n"
 
 
 def _safe_pkg_dir(raw: str) -> Path:
@@ -456,7 +469,7 @@
         "confirm": True,
         "kernel": kernel,
         "version": str(args.get("version") or "1"),
-        "file": str(args.get("file") or "arc-agi-3/kaggle/results/submission.parquet"),
+        "file": str(args.get("file") or "submission.parquet"),
         "message": str(args.get("message")
                        or "arc3-duck-original: Tufa Labs duck harness (June 30 milestone winner, public MIT) rerun by petersharps; attribution: Tufa Labs / jeroencottaar"),
     }


candidate-45 — jeden kandydat zamiast pięciu gałęzi
Ten katalog scala to, co w repo jest zweryfikowane, i dokłada jedną rzecz, której nie ma nigdzie: sondę rosteru — odpowiedź na pytanie, czy 110 runów to 25 mechanik × ~4,4 repliki. Jeśli tak, to jest jedyna dźwignia, której rozmiar zamyka lukę 208 akcji vs 685 potrzebnych.

Uczciwie na wejściu: to nie jest „super-wersja, która daje 45+”. To jest kandydat, który (a) usuwa blokery, (b) odzyskuje część budżetu, (c) w jednym runie odpowiada, czy mnożnik ~4,4 istnieje. Żaden element scoringu nie jest tu zmięrzony — jedyne zmierzone liczby w repo to 27,21 (smoke r019) i 26,25 (LB). Oczekiwanie na tym pakiecie: 27–34 na pierwszym runie. 40+ wymaga wyniku sondy = CYCLIC albo podniesienia MAXREQ. Szczegóły w sekcji 5.

1. Co jest w środku
plik	co robi	stan
patches/0006-ops-submit-filename.patch	naprawia -f w ops.py: auto-submit podawał ścieżkę zamiast nazwy pliku (400 CreateCodeSubmission) i dodaje normalizację + odmowę na pusty -f	zweryfikowany
notebook/arc3-duck-c45.ipynb	notebook z łańcuchem franzen → 0001 → 0002 → 0004-standalone (bez ich 0003, które wywala cell 9) + hook w cell 21	zbudowany z arc3-duck-fixed.ipynb
notebook/cell21_candidate.py	hook: sonda rosteru + ARC3_LEVEL_TOKEN_CAP	4 testy, fail-soft
tools/analyze_roster.py	zamienia roster_probe.jsonl w werdykt CYCLIC / DISTINCT	przetestowany na obu symulacjach
tests/test_ops_submit_filename.py	5 testów na bug -f (na oryginale 4 padają)	przechodzi na poprawce
verify.sh	łańcuch patchy + py_compile + testy 0004 + testy ops + testy hooka + build notebooka	WSZYSTKO OK
Czego nie robi ten pakiet: nie rusza llm-agent, nie zmienia modelu, nie włącza replay (n_passes=1 + ONLY_RESET_LEVELS=true → replay ≈ 0), nie dokłada własnych narzędzi modelowi.

2. Co dokładnie naprawia
2.1 -f — jedyny bloker, który zjada sloty codziennie
ops.py w gałęzi auto-submit miał:

python
Copy
"file": str(args.get("file") or "arc-agi-3/kaggle/results/submission.parquet")
Kaggle CLI przyjmuje w -f nazwę pliku wyjściowego kernela. Ścieżka kończy się 400 CreateCodeSubmission, zanim cokolwiek innego jest sprawdzane. Dowód z Waszych danych: r048 i r049 miały status COMPLETE i mimo to 400 — czyli to nie status wersji, tylko argument. 12 prób ze ścieżką → 12× rc=1; 2 próby z nazwą → 2× rc=0.

Patch normalizuje w op_submit (jedynym miejscu, które dotyka CLI), więc nie zależy od tego, co poda wywołujący, i zostawia ślad w wyniku (UWAGA: ...).

2.2 Łańcuch patchy — bez run-killera
0003 (ich duck-extra-02.patch) był generowany względem oryginalnego solver.py, a cell 9 nakłada patche po patchu Franzena z check=True. Efekt: patch does not apply → CalledProcessError → notebook umiera przed pobraniem wag. Potwierdzone w verify.sh na drzewie 42 plików z r033.

Zalecany łańcuch: franzen → 0001 → 0002 → 0004-standalone. Nie dokładać 0003b, bo 0004 wchodzi w ten sam rejon solver.py.

2.3 Cap per poziom — włączony, ale niezmierzony
0004-standalone daje budżet tokenów na poziom, darmowy RESET po jego przekroczeniu i dopiero po ARC3_LEVEL_RESETS_MAX porzuca grę. W notebooku c87 stoi już ARC3_LEVEL_TOKEN_CAP=45000, ARC3_ABANDON_TOKENS=0, ARC3_LEVEL_RESETS_MAX=1 — hook nie nadpisuje tych wartości, tylko je raportuje.

Mechanizm jest opisany poprawnie (oddanie slotu przenosi przepustowość na inną grę w puli 10 strumieni), ale szacunek +7…+17 pkt jest przeszacowany: to wymaga, żeby odzyskane tokeny trafiły w gry blisko progu poziomu. Realnie: +0 do +3, z ryzykiem regresu przy złym capie.

2.4 Sonda rosteru — nowe, i to jest sedno
official_110() (competition_arcade.py:100) to source_infos[i % 25], a każdy klon dostaje tag taaf_source_game:<id>. Czyli lokalnie roster jest cykliczny: 110 runów = 25 mechanik × 4,4. Pytanie brzmi, czy prywatny roster też — i tego nie da się sprawdzić inaczej niż w prawdziwym submisie.

Hook loguje do /kaggle/working/roster_probe.jsonl dla każdego runu: game_id, index, pass_index, hash pierwszej ramki, win_levels, available_actions, a na końcu levels, actions, hash ostatniej ramki. Koszt: 0 dodatkowego GPU — jedzie z submisem, który i tak wysyłacie.

3. Jak użyć
bash
Copy
# 1. weryfikacja offline (bez GPU, bez Kaggle)
bash candidate-45/verify.sh

# 2. ops: naprawa submitu - patch jest robiony z katalogu, w ktorym lezy ops.py
cd arc-agi-3/kaggle/ops
git apply <sciezka>/candidate-45/patches/0006-ops-submit-filename.patch   # => -f submission.parquet
cd - && OPS_PY=arc-agi-3/kaggle/ops/ops.py python3 candidate-45/tests/test_ops_submit_filename.py

# 3. notebook: wgraj candidate-45/notebook/arc3-duck-c45.ipynb na Kaggle
#    (GPU: RTX PRO 6000, wszystkie inputy zostawione jak w oryginale)

# 4. po runie
python3 candidate-45/tools/analyze_roster.py roster_probe.jsonl
4. Kill-switche
co	jak wyłączyć
cap per poziom	ARC3_LEVEL_TOKEN_CAP=0 (env w cell 1)
sonda	usunąć blok _install_roster_probe() z cell 21; nic innego jej nie woła
zmiana ścieżki logu	C45_PROBE_OUT=/kaggle/working/inne.jsonl
Cały hook jest w try/except: brak numpy, brak inference.framework.solver, sesja bez game_run, niezapisywalny katalog — każde z tych zdarzeń kończy się wpisem error albo cichym pominięciem, nigdy wyjątkiem w runie. To jest przetestowane (tests/test_cell21_probe.py, w tym przypadek /proc/nie/ma/takiej/sciezki.jsonl).

5. Plan runów i budżet GPU (quota 30 h/tydz., 1 submit/dzień, finał 2 XI)
bramka	co	koszt	co rozstrzyga
G1	smoke 10 gier × 48 min na kandydacie	2,5 h	czy łańcuch patchy + hook nie wywalają runu; poziomy ≥ r019
G2	jeden prawdziwy submit z sondą	9 h	(a) czy -f naprawiony, (b) CYCLIC czy DISTINCT, (c) wynik z capem
G3a	jeśli CYCLIC → pamiec miedzy replikami	patch + 1 smoke 2,5 h	czy ×4,4 realnie podnosi głębokość
G3b	jeśli DISTINCT → MAXREQ=16 + krótsze okno	1 smoke 2,5 h	czy +45% puli przekłada się na +1 poziom
G4	finalny submit	9 h	wynik
Razem ~23 h z 30. Jedna zmiana na bramkę — inaczej znowu będzie wiadomo, że „coś” zmieniło wynik, ale nie co.

6. Czego ten pakiet NIE obiecuje
Nie ma tu 45+. Jedyna zmierzona liczba to 26,25 na LB. Wszystko powyżej jest hipotezą z jawnym rozmiarem i jawnym ryzykiem.
Cap 45000 może zaszkodzić. Historia v6 uczy, że dokładanie decyzji kosztowych na stałej puli obniżyło LB (23,94 vs 24,66). Dlatego G2 mierzy też poziomy per gra, nie tylko średnią.
MAXREQ to ekstrapolacja, nie pomiar. 792 tok/s przy 10 strumieniach jest zmierzone; ~1150 przy 20 — nie.
Pamięć między replikami nie jest zaimplementowana. ARC3_PERSISTENT_FUNCTIONS_SCOPE przyjmuje tylko turn|levelup|game — wartość run nie istnieje i po cichu spada do levelup. To wymaga patcha, nie zmiennej env. Najpierw sonda.
Nie wysłałem nic na Kaggle i nie użyłem żadnego klucza. Bez Twojego runu ten pakiet jest kodem, nie wynikiem.