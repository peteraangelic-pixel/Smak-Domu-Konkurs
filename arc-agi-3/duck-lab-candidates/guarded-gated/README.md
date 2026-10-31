# Codex v3 guarded-gated: eksperymentalny kandydat

SHA256 notebooka: ad163283ffe7c6c63ddb5e0e3ac63b27950308c6cee761be2e7e70c72d723d85.

Baza: dokładna odzyskana v3,historyczne26.25; kontroler Codex template; guard i pakowanie Gemma c4/acb2a95; single-mismatch gate Gemma6d/004769ec. Ten notebook ma nowy slug i **nie ma wyniku Kaggle**. Nie jest v11-hint ani v13.7. Pozostawia oryginalny fallback LLM.

Zmiana względem Gemma v17: bramka dopuszcza ścieżkę identycznej pieczęci tylko przy dokładnie jednej niezgodnej komórce. Guard32 ogranicza propozycje na poziom; ARC3_TEMPLATE=0 deleguje do oryginalnego analyze. Bramka nie obejmuje całej indukcji reguł i nie dowodzi bezpieczeństwa na wszystkich nieznanych grach.

Własne pomiary:

- 25/25 par śladów na publicznych grach zgodne z samym guardem;3 ukończenia/25 akcji ft09,w pozostałych24 abstynencja.16 procesów,Rust FFI w ekstrakcji prostokątów.
- 2400 syntetycznych przypadków: oryginał/bramka,po300 na copy/rotate/invert/random. Copy149/149 zachowane; rotate299/18→17/3,invert300/0→0/0,random297/23→8/1. Rozpoznane/trafne; nie są to statystyki ukrytego rosteru.
- Pełny łańcuch patchy odtworzony na r033; wszystkie źródła inference kompilują się.
- Gotowy notebook przez rzeczywisty Duck/sandbox w controller-only:3 poziomy,25 akcji,około4.95s,0API,oracle=false,error=null. Stop przy abstencji jest celowy; całej gry nie ukończono. Ten test nie sprawdza fallbacku z docelowym modelem.

**Poprawa zabezpieczeń,nie zmierzony wzrost ukończeń.** Brak target Flash-Next A/B i podstaw do prognozy59+. Brak dodatkowej zdolności do nowych mechanik. Nie wysłano na Kaggle.

Odtworzenie z katalogu projektu:

```powershell
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/build_guarded_gated.py
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/verify_gated_candidate.py
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/benchmark_causal_explorer.py --workers 16 --variants guarded gated --rect-backend rust --actions 160 --out NOWY_PLIK.jsonl
```

Rust DLL jest przyspieszeniem offline; notebook korzysta z przenośnego wariantu NumPy.

Dane: analysis/navigation-20261031/guard-gate-public25.jsonl,gated-safety.json,packaged-harness/{result,manifest,game-run}.json.

Nieudany eksperyment obok: dwa nawigatory oparte na tłumaczeniu sprite'a i eksploracji mapy,po25 rzeczywistych gier,0 ukończeń. Nie dołączono ich do notebooka. Dane public25-v1/v2.jsonl są negatywnym wynikiem,nie kandydatem do submisji.
