# Niezależna ablacją zakresu funkcji

Baza: dokładna v3,nie slim. Jedyna zmiana polityki: ARC3_PERSISTENT_FUNCTIONS_SCOPE game→levelup. ARC3_MEMORY_SECTIONS pozostaje OFF. Model,budżet,roster,serwowanie i temperatura pozostają bez zmian. Bez odrzuconej pamięci ukończonych poziomów i recovery.

Hipoteza: po przejściu poziomu stare funkcje mogą kodować nieaktualną geometrię/kolory. W logu slim/s5i5 helper run po zmianie poziomu szukał koloru Y,którego nowa plansza nie miała. To trop infrastrukturalny,nie dowód przyczyny wyniku. Ryzyko: usunięcie poprawnych wspólnych parserów i dodatkowy koszt ich odtworzenia. Usunięcie funkcji nie usuwa całej historii rozmowy.

Implementacja upstream,bez nowych patchy. verification.json potwierdza rzeczywiste metody ToolAgent: retencję wewnątrz poziomu,czyszczenie na przejściu,komunikat czyszczenia,odmienne zachowanie kontroli game i izolację przez katalog runtime. Pierwszy test pomylił różne nazwy plików z różnymi katalogami sesji;poprawiono fixture,nie agenta. 34 źródła inference identyczne z kontrolą,14 komórek kompiluje się,3 patche stosują się czysto.

Komendy od korzenia repo: python arc-agi-3/analysis/build_v3_levelscope.py; python arc-agi-3/analysis/materialize_duck.py arc-agi-3/duck-lab-candidates/v3-levelscope/agent.ipynb <nowy_katalog>; python arc-agi-3/analysis/verify_levelscope.py. Weryfikator używa stałego katalogu materialized zapisanej próby;do ponownego clean materialize wybrać nową ścieżkę.

Ocena: ukończenia per gra i grupy,rzeczywiste komunikaty czyszczenia,nowe zera,błędy,score i tokeny. Obiecujący wynik wymaga świeżej kontroli. Żadnej automatycznej submisji konkursowej.
