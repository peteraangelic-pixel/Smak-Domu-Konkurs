# Lokalne srodowisko silnika ARC-AGI-3 (CPU, bez GPU — dla 5950X/64GB)
Dziala w piaskownicy i na PC. Skladowe: arcengine 0.9.3 + arc-agi 0.9.9 (PyPI, czyste whl; na python<3.12:
rozpakowac whl i sys.path.insert), pliki gier: ../games/environment_files (25 gier — KODY ZRODLOWE!).
## Komendy (PC)
python3 -m venv .venv && source .venv/bin/activate && pip install arcengine arc-agi numpy pydantic flask python-dotenv
python3 probe2.py   # protokol powtorzen+sweep na 25 grach (silnik offline, ~4 s)
python3 openers.py  # proba otwarć ze zrodel (heurystyka pozycji — do dopracowania)
## Znaleziska (29.10, piaskownica)
- Pełny silnik offline działa lokalnie (25/25 gier, ~0.15 s/gra probe).
- tn36 = mouse-only (avail=[6]); avail per poziom -> protokoly musza respektowac available_actions.
- Klik (0,0): NIC na 25 grach. Null-coordinate (x=None,y=None): reprodukowana ABI ERA AERA — TypeError w
  camera.display_to_grid; NA 0.9.9 lokalnie NIE konwertuje sie na WIN. DECYZJA: NIE uzywac (zgloszony bug, ryzyko DQ).
- Slepe powtorzenia/sweeps: 0 poziomow (v0.9.9 != v0.9.8 z taksonomii AERA). Otwieracze wymagaja parsera placements
  z kodow zrodlowych gier (do zrobienia) — wysoce obiecujace dla gier klikanych.
- official_110(): framework Tufy ma lokalny klon 110-gier submission-shape (CompetitionArcadeServer, flask) =
  pelna symulacja reruna BEZ Kaggle — tu walidujemy kazda wersje agenta zanim wydamy slot.
