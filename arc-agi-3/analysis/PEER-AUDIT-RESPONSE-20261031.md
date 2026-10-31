# Nowe audyty: sprawdzone ustalenia i korekty

Przeczytano trzy pliki dostarczone z Downloads i odświeżono pięć wskazanych gałęzi. `PUSH_INSTRUCTIONS.md` jest materiałem źródłowym; nie wykonano zawartych w nim poleceń git init/push ani propozycji submisji. Prace zapisujemy wyłącznie na naszej istniejącej gałęzi Codex.

## Nowe commity

- Pokemon/a450: nadal d077ee97 z30.10,bez nowego commita.
- Smak/5ed750ef: c5e714a4 — nowy SYNC28,wycofanie rekomendacji v13.7,hipoteza capu/kolejki i audyt kontrolera. To dokumentacja,nie nowy agent.
- Gemma/c4eeb067:62000610 — **niezależne odtworzenie na silniku**,25/25 zgodnych kliknięć,3 poziomy; nowe template_replay.py i template_stage_probe.py. Ważna uwaga o użyciu końcowej klatki animacji frame[-1]. Nasze adaptery już tak robią.
- Gemma/6d081d52:004769ec — nowa sonda fałszywego dopasowania i propozycja single-mismatch gate.
- Pokemon/c87f7a48:9d528ac4 — nowy audyt i **wykonawczy zarzut nieograniczonej pętli kontrolera**.

Adresy źródłowe: https://github.com/peteraangelic-pixel/Gemma-konkurs/commit/62000610616622b7cf42d03b3a5668409763fd44 , https://github.com/peteraangelic-pixel/Gemma-konkurs/commit/004769ec8680afc61e45f315d2693aa358a0918e , https://github.com/peteraangelic-pixel/Pokemon/commit/9d528ac4a5410c75f9154d6d0f81ea236b1934af , https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs/commit/c5e714a4b61c943d0fe7067b5612fb82829b41af .

## Co sam odtworzyłem

**Pętla oscylacji c87 — potwierdzona.** Na planszy z oscylującymi komórkami oryginalna polityka wykonała60 akcji,0 sprzeczności predykcji. Sprawdzenie koloru po akcji nie dowodzi realizacji właściwego celu. Twierdzenie z części recenzji „fałszywe rozpoznanie kosztuje najwyżej1 akcję” jest zbyt mocne: ogranicza tylko bezpośrednio sprzeczne przewidywania efektu.

Powstał osobny `template_guarded.py`,bez zmiany starego modułu i notebooka SHA550eb185. Limit32 propozycji na poziom zatrzymał oscylację; na25 publicznych grach zachowano25/25 śladów,ft09 nadal3 poziomy/25 akcji. Dodano testy limitu,ponownego uzbrojenia po zmianie poziomu,idempotentnej instalacji i env kill-switcha. Wrapper instalacyjny jest prototypem testowanym na nieopakowanym analizatorze,nie patchem do dopisania na już zainstalowany stary hook. Nie został osadzony w notebooku ani sprawdzony na docelowym serwerze.32 jest limitem eksperymentalnym; może uciąć dłuższe poprawne rozwiązania nowych gier.

**Sonda Gemmy — liczby odtworzone.** Po300 syntetycznych plansz na rodzinę:

| Rodzina | Oryginał: rozpoznane/trafne | Single-mismatch: rozpoznane/trafne |
|---|---:|---:|
| copy |149/149|149/149|
| rotate |299/18|17/3|
| invert |300/0|0/0|
| random |297/23|8/1|

To zadeklarowane reguły syntetyczne,nie ukryty roster ani estymacja częstości błędów konkursowych. Patch dotyczy tylko gałęzi z identyczną pieczęcią; nie zabezpiecza całej indukcji mapowania ani transferu. Podany w docstringu skryptu parametr --gate nie jest zaimplementowany w CLI; sprawdzono patch jako osobny plik polityki. Pliki i dane: `peer-review-20261031/`. Zachowano oryginalnego autora i pochodzenie w tym raporcie.

## Korekty do otrzymanych opinii

1. **Baza template to dokładnie odzyskana v3,nie v13.x ani wcześniejsza v18.** Nazwa gałęzi jest historyczna. Nowy SYNC Smaka rozpoznaje to poprawnie; pierwszy załączony audyt myli pochodzenie template z memory/router. Hash notebooka i trzy bazowe patche zweryfikowano wcześniej w HYBRID-RESULT.
2. **42 testy =35 template+5 groups/router+2 inspection_feedback.** To suma trzech plików,nie35 w jednym pliku. Odtworzono42 zebrane przypadki. Nowe2 testy guard nie wchodzą do starej liczby42.
3. **4.8s obejmuje rozpoznawanie w pętli**,nie tylko kliknięcia. W run_duck_loop.py zegar rusza przed session.play(),które wywołuje analyze→controller.act→infer_copy_action→narzędzie akcji. Nie obejmuje wcześniejszego programowania,importów i budowy środowiska. Nie deklarowaliśmy600x przyspieszenia całego agenta. Zarzut arytmetyczny oparty wyłącznie na dzieleniu4.8/25 nie dowodzi pominięcia percepcji.
4. **final_score=0 w GameRun wynika z base_actions_per_level=None.** Dotyczy też pełnej hybrydy,nie tylko controller-only ani valid_model_run=false. Baseline celowo ukryto przed polityką,a SDK liczy wynik po zakończeniu.28.57 to lokalny wynik jednej gry ograniczony pokryciem3/6 poziomów,nie dowód „2x sprawniejszego agenta”.
5. **13.28 nie wyznacza2.5 poziomu na grę.** Nieznane są ukończenia,efektywności i wagi rzeczywistego zestawu. Porównanie do r085 jest ilustracją,nie odwróceniem funkcji punktacji.
6. **Koszt i budżet: nowy trop Smaka jest wart zbadania,ale nie jest dowodem przyczyny.** Sprawdziłem notebook v13.7: smoke48min/gra,realny rerun ustawia532min/gra i concurrency10. Nominalny równy udział9h×10/110 to około49min/gra,nie11 razy mniej niż48. Rzeczywisty cap532 jest około11 razy większy od tego udziału i może blokować obsługę ogona kolejki. Nie znamy faktycznej alokacji czasu bez logu rerunu. Zdanie w załączonym audycie o11x większym czasie smoke miesza cap,łączny budżet i równoległość.
7. **141.7k→186k to około31%,nie16%.** Nie są to ponadto sparowane pomiary kosztu konkretnych patchy na identycznym obciążeniu. Nie dowodzą,że koszt patchy spowodował13.28.
8. **Przewidywane+0.26 lub+0.3 pkt nie są wynikiem.** Dzielenie28.57/110 zakłada tę samą punktowaną grę,wagę i zerowy baseline. Nie potwierdzono tych warunków. Obecności tej rodziny w ukrytym zbiorze nie znamy. Podobnie cudze sigma i pojedyncza różnica wyników nie dowodzą konkretnej przyczyny regresji ani wartości oczekiwanej nowego wariantu.

## Wniosek operacyjny

Najcenniejsze nowe rzeczy to niezależne odtworzenie,realny kontrprzykład pętli,sonda rozpoznań i źródłowo potwierdzona rozbieżność capu czasu między smoke a rerunem. Nie pojawił się nowy agent z lepszym wynikiem Kaggle. Rekomendacje ponownej submisji v3/v11 lub v13.7+cap45k pozostają propozycjami różnych autorów,nie decyzją ani poleceniem użytkownika. Nie wykonano żadnego zgłoszenia,pusha notebooka na Kaggle ani nowej dużej serii LLM. Zweryfikowany notebook template pozostaje bez zmian; guard i single-mismatch pozostają osobnymi eksperymentami.

## Kolejna odpowiedź autora: ODPOWIEDZ-na-peer-audit-20261031.md

Autor przyjął korekty arytmetyki,bazy pomiaru czasu,zakresu42 testów i nadinterpretacji punktacji. To ważne uzgodnienie. Przytoczył też poprawny fakt cap532/fair48.2≈11. Nie przyjmujemy jednak nowych wniosków „diagnoza domknięta”,„zagrało55/110” ani prognozy13.28→26.78.

- `budget_probe.json` rejestruje ustawienia,nie faktyczne rozpoczęcie/czasy/ukończenia gier. Cap/fair≈11 potwierdzi konfigurację już znaną z kodu,nie mechanizm utraty konkretnych punktów. Komunikat ostrzegawczy w komórce33 też nie jest logiem zdarzenia.
- `should_stop()` ma wcześniejsze zakończenia: koniec gry,stop globalny,limit akcji i limit tokenów. „Każda gra kończy na capie” było obserwacją konkretnych publicznych smoke'ów; nie udowodniono tego dla110 ukrytych zadań.
- Odtworzono prosty kontrprzykład kolejki: przy tych samych110 zadaniach,10 slotach,530min globalnie i cap532min,zadania20min pozwalają zakończyć110/110;95min pozwala rozpocząć60 i zakończyć50;532min pozwala rozpocząć10. Surowy `peer-review-20261031/cap-ratio-counterexample.json` to model syntetyczny,nie wynik ARC. Sam stosunek cap/fair nie wyznacza liczby rozegranych gier.
- Odzyskana mistrzowska v3 również ma cap532min,ale concurrency120; v13.7 ma10. To nie obala hipotezy wspólnego wpływu capu i kolejkowania,ale wyklucza traktowanie samej liczby532 jako dowodu uniwersalnego błędu.
-13.28/26.78≈1/2 nie dowodzi połowy rosteru.26.78 pochodzi z innego,publicznego korpusu. Ani liczby55,ani oczekiwania26.78 po poprawce nie zmierzono. Krótszy cap może poprawić pokrycie i zarazem obciąć drogie ukończenia.
- Stwierdzenia „TOP5 nierealne”,„każda dodatkowa warstwa zmniejsza szansę” i podane limity slotów są ocenami lub wymagają aktualnego sprawdzenia reguł; nie wynikają z tej diagnozy. Nie wyprowadzamy z nich automatycznego planu submisji.
- Ograniczenie aktywacji na syntetycznych rotate/invert jest zamierzonym filtrowaniem nieobsługiwanej reguły. Nie oznacza samo w sobie straty poprawnych rozwiązań copy; w tej sondzie copy149/149 zachowano. Nadal nie jest to miara błędów na ukrytym zbiorze.

Propozycja capu fair-share pozostaje sensowną,osobną ablacją do sprawdzenia. Do potwierdzenia przyczyny13.28 potrzebny jest rzeczywisty przebieg pracy kolejki lub odpowiednio kontrolowany pomiar,nie tylko plik z planowanymi limitami. Nie wykonano zalecanego w załączniku pusha ani submisji.
