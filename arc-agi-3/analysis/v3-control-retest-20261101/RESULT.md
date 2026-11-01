# Identyczna v3: duża zmienność,brak potwierdzenia przewagi scope

Kontrola2 COMPLETE:38 ukończeń/36.09039,ARC3_SMOKE_OK,crashed=[],1,771,848 tokenów. Ten sam notebook SHA8d0195f9…7bcc co kontrola1:33/27.49667. Różnica bez zmiany kodu:+5 poziomów/+8.59372 punktu publicznego. Nie jest to wynik konkursowy ani zmierzony rozkład wariancji z wystarczającą próbą.

Scope1:36/29.89804 mieści się pomiędzy kontrolami. Poprzedni wzrost względem kontroli1 nie wystarcza do wniosku o poprawie. Nie promować scope jako zwycięzcy. Szczególnie su15 kontrola3→7,tn36 3→1,s5i5 5→2;duża zmienność między grami nie jest objawem zmiany kodu.

Następny test:odrębny v3-hypotheses na dokładnej v3,bez scope/slim/recovery. Wysyłany SHA7fff0787f3ec9442ce26aa6e74807b5eaabfaa8ae0a8d681184786c83a61d1b4. Jeden patch dodaje helpery rozróżniania/walidacji hipotez i opis API. Clean patch chain oraz rzeczywisty izolowany sandbox przeszły. W teście docelowym koniecznie sprawdzić rzeczywiste HYPOTHESIS_PROBE i HYPOTHESIS_VALIDATE w wynikach narzędzi,nie w echoed źródle. Brak aktywacji oznacza nieudaną integrację protokołu,nie dowód nieskuteczności aktywnego planera. Porównywać z obiema kontrolami;obiecujący wynik wymaga replikacji.
