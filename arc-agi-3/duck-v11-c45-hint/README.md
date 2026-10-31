# v11-hint: kandydat A i niezmieniona kontrola

Status: pakowanie i łańcuch patchy zweryfikowane; jakość niezmierzona. Brak nowego wyniku Kaggle i rekomendacji submisji.

Kandydat: ten folder. Kontrola: sąsiedni `duck-v11-c45-control`. Każdy zawiera notebook i kernel-metadata.json z osobnym prywatnym identyfikatorem. Kontrola jest dokładnym notebookiem bazowym v11; jej metadane zmieniają tylko id/title. Kandydat zmienia wyłącznie ARC3_OPENER_COMMIT_HINT=1 oraz opis/nazwę wariantu. Nie dodaje template, routera ani nowego capa. Zachowuje cap45000/reset1/min_done0, PLAN_COMMIT=0, concurrency10 i 532min/gra w rerunie. To ablacją hintu,nie naprawa harmonogramu.

Sprawdzenia: 33 komórki,18 komórek kodu kompiluje się; pięć patchy stosuje się na czystym r033; wszystkie wynikowe źródła inference są identyczne z kontrolą. Wcześniejszy test AST potwierdził aktywację wskazówki. PAIR-MANIFEST.json zawiera hashe notebooków i zakres weryfikacji. Są to sprawdzenia infrastruktury,nie gry z modelem.

Odtworzenie z głównego katalogu projektu:

```powershell
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/duck-v11-c45/tools/build_env_variant.py --profile hint
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/duck-v11-c45/tools/verify_env_variant.py --pkg arc-agi-3/duck-v11-c45-hint
```

Następny pomiar wymaga dwóch świeżych prywatnych uruchomień Kaggle na tym samym docelowym Flash-Next i drafterze. W obu smoke: ten sam roster10 gier,48min/gra,concurrency10. Nie porównywać do historycznej26.25 ani traktować smoke jako wyniku konkursu. Porównać roster,ukończone poziomy każdej gry,tokeny,akcje,awarie oraz ściany czasu. Zero ukończeń/przewagi nie uzasadnia promocji. Różne mechaniki ocenić osobno; strata ukończenia wymaga analizy. Pojedyncza para nie gwarantuje wyniku ukrytego zestawu.

Nie uruchomiono nowego wielogodzinnego testu Qwena: wcześniejsze zerowe kontrole nie dają mu potwierdzonej zdolności wybierania lepszego wariantu Flash-Next. Nie deklarujemy wzrostu punktów ani miejsc premiowanych.

Przed uruchomieniem zdalnym potrzebna osobna zgoda użytkownika,który wcześniej zastrzegł publikowanie/zgłaszanie notebooków na Kaggle. Prywatny kernel push uruchamia notebook i zużywa zasoby Kaggle; nie jest submisją konkursową. Te operacje pozostają rozdzielone. Nie wykonano żadnej z nich.
