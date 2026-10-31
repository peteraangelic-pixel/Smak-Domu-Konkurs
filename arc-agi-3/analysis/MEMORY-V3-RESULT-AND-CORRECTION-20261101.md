# Pamięć v3: wynik wersji1 i osobna korekta wersji2

Wersja1 zakończona COMPLETE. Publiczny smoke: **28.39998,32 ukończenia** wobec kontroli27.49667/33. Pamięć rzeczywiście działała:31 linii capture,22 pinned,0 błędów hooka,ARC3_SMOKE_OK.

**Wersja1 nie przechodzi bramek submisji:** mniej niż wymagane34 ukończenia i nowe zero tn36 (kontrola3 poziomy). Nie obniżamy kryteriów dlatego,że wzrosła średnia. To nie jest nowy wynik konkursowy.

Per gra ukończenia:tn36 0,m0r0 4,cn04 3,dc22 3,ka59 4,sc25 6,s5i5 2,ls20 4,su15 4,g50t 2. Efekt nie jest jednolity; pojedyncza para nie rozstrzyga przyczynowości.

## Diagnoza i hipoteza korekty

tn36 wykonało869 akcji,w tym15 RESET. Z historii odtworzono14 odrębnych zamkniętych prób; nie są identycznymi sekwencjami. Pierwsze13 miało po61 akcji,ostatnia też zakończyła się wyczerpaniem czasu. Ostatni prompt pokazuje śmierć i reset na poziomie1. Nieukończenie poziomu1 oznacza,że pamięć rozwiązanych poziomów nie miała tam jeszcze materiału. **Nie przypisujemy tego zera przyczynowo pamięci.**

Nowa falsyfikowalna hipoteza: po trzech długich nieudanych próbach o prawie tej samej długości krótki audyt może skierować model z kolejnej długiej trasy na rozstrzygający eksperyment i plan. Powtarzalna długość sugeruje budżet ruchów,ale nie dowodzi przyczyny śmierci; tekst wymaga sprawdzenia paska i modelu.

Wersja2 = wersja1 + jedna ograniczona wskazówka po nieudanej próbie,tylko gdy3 ostatnie próby mają>=30 akcji i różnią się długością najwyżej2. Maksymalnie raz na grę/poziom. Nie wykonuje ruchów,nie kończy gry,nie włącza nowego capa ani nie zakłada identyfikatora gry. Nie zmieniać jej po zmierzeniu.

Weryfikacja:pełny chain na r033,kompilacja,pamięć po rzeczywistym ukończeniu ft09,przycięcie tokenowe i limitem wiadomości,izolacja między grami. Wykonano rzeczywiste funkcje AST nowego hooka:trzy długie równe próby aktywują;druga wskazówka,krótkie/nieregularne/dwie próby i brak game_over nie aktywują. To testy infrastruktury,nie dowód poprawy LLM.

Kod:memory_v3_recovery.py. Paczka:duck-lab-candidates/memory-v3-recovery. Metadane kierują na TEN SAM prywatny slug jako następną wersję2. Builder tworzy domyślnie osobny slug; na potrzeby tego testu jawnie ustawiono id=petersharps/arc3-codex-memory-v3-lab. Wersja1 i jej wyniki są zachowane. Kontrola,model,roster i budżety pozostają identyczne. Przed pushem skrypt sprawdza,czy najnowszy kod nadal odpowiada wersji1,aby nie nadpisać istniejącej korekty.

SUBMISSION-CANDIDATE.json nadal wskazuje wersję1; **nie jest zakwalifikowana**. Dopiero po zakończeniu i przejściu wszystkich bramek wersji2 wolno przepiąć konfigurację na jej numer,plik i hash. Nie zgłaszać z tego monitora;decyzja o02:10 pozostaje osobną automatyzacją.

Surowe wyniki wersji1:analysis/memory-v3-target-20261031/result-download/ oraz result-summary.json. Test korekty:recovery-activation/result.json,recovery-isolation.json,recovery-hint-check.json w tym samym katalogu.
