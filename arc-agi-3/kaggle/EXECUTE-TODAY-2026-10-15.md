# EXECUTE TODAY — slot 15.10 (decyzja usera: „wrzuć to co polecasz")

Rekomendacja bez zmian: **duck @200k**. UWAGA: galez 98ddb59f stoi od 13.10 12:04 —
wczorajszy slot NIE zostal uzyty (sprawdzone: brak commitow po 148be97).
**Tylko JEDEN tor wykonuje push (zero podwojnego spalania).**

## TOR 1 (PRIMARY) — galez 98ddb59f (duck owner)
Znacie dokladne pokretlo z krzywej (100k→24.7, 200k→41.8) i macie CI+sekrety.
Zadanie na dzis: push waszego kernela duck z budżetem 200k tok/grę (slot 15.10).
MECHANIZM POTWIERDZONY (weryfikacja 15.10 00:55, potwierdza wasza wiadomość):
**arc3-ops.yml** = jedno CLI do wszystkich operacji Kaggle. Fire: edycja
`arc-agi-3/duck/ops/request.json` ({"id","op","args"}) + push na 98ddb59f
lub dispatch. Wasz op `submit` jest chroniony w kaggle_ops.py: COMPLETE save
run + smoke marker + wolny limit dzienny (dokładnie nasz „check-output przed
Submitem" — jesteście pod tym względem ok). Łańcuch z 12–13.10: 0f1f212
(push kernela v2-think-less) → f853f73 (r008 submit, run 38329969972, SUCCESS,
→24.66). Dziś: r020 = build/run duck @200k, potem submit (guardy zrobią swoje).
My nie możemy pisać do waszego repo (403) — request.json edytuje wasza sesja.

## TOR 2 (FALLBACK — user, 1 komenda), gdy tor 1 nie ruszy do południa
Gotowiec w tym katalogu: `submission.ipynb` = fork publicznego share-notebooka
Tufa (MIT, dataset publiczny: 4137 pobrań; społeczność resubmitowała — złote
medale za forki) z hookiem cell-12: runtime ≥60 min/grę, bez ciecia akcji,
label `-long200`. Datasety publiczne (3x) już w kernel-metadata.

```
cd Smak-Domu-Konkurs/arc-agi-3/kaggle/duck-200k
kaggle kernels push -p .
# Kaggle -> Code -> wybrac akcelerator zgodny z wheelhouse (H100; bez H100 nie pushowac)
# po zakonczeniu runu (~godziny): sprawdzic output (25 gier, brak placeholderow)
# dopiero wtedy Submit w UI zgloszenia
```

| Wariant | Expected | Ryzyko |
|---|---|---|
| Tor 1 (ich 200k knob) | **~41.8** (krzywa) | niskie (sprawdzona rura) |
| Tor 2 bez ich knobu (long-runtime) | ~24.7+ (floor) | niskie; slot nie zmarnowany |
| Tor 2 + 200k knob od toru 1 (2 linie w hooku) | ~41.8 | niskie |

## NIE robić dziś
- Nie pushować naszego notebooka vLLM (v6.9) — zero pomiarów rury; jego czas:
  paired A/B po 17.10 (GOAL_CLASS 0/1, 2×10 gier).
- Nie wrzucać ich v7.0 — brak pomiarów, adapter nigdy nie biegł e2e.
- Nie wykonywać obu torów naraz.
