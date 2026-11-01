# Port CPU: najpierw kopiowanie stanu

Sprawdzono zainstalowany arcengine:7 plików Python,2342 linii. Publiczne25 środowisk:118782 linii kodu ORAZ danych;nie wszystkie są logiką przejść. Przepisanie samego API silnika nie przenosi logiki gier do Rust.

Aktualny pomiar cProfile na ft09,worker(CONTROL,node_cap120,sec_cap1,max_levels1),podczas16-procesowej ewolucji:całość3.783s,deepcopy2.831s,perform_action0.534s,search_level2.891s. Są to koszty kumulacyjne,zagnieżdżonych wierszy NIE sumować. Profilowanie i konkurencyjne obciążenie zaburzają czasy;to wskazówka hotspotu na jednej grze,nie uniwersalny speedup. Limity czasu węzłów są miękkie,więc sec_cap1 nie oznacza całej pracy w1s. Surowy profil:cpu-search-20261101/ft09-profile.txt.

Wniosek:przed pełnym portem silnika sprawdzić zwarty snapshot/copy-on-write lub reset+replay w osobnym pliku backendu. NIE zmieniać sweep2.py/native_kernels.py ani kodu bieżącej ewolucji podczas aktywnej macierzy:worker importuje je z dysku,a manifest przypina ich hashe.

Warunki poprawności nowego kopiowania:rodzic i dwoje dzieci izolowane,poprawne RESET/GAME_OVER/przejście poziomu;identyczne ramki końcowe i pośrednie,legalne akcje i ukończenia przy tej samej sekwencji. Najpierw1 gra,następnie cały publiczny korpus. Żadnego zakładania niezmienności danych bez testu;nie współdzielić mutowalnych Sprite/Level między gałęziami.

Rayon nadaje się do niezależnych stanów/partii,ale nie przyspiesza automatycznie sekwencyjnej zależności ruchów. Obecne16 procesów używa Rust FFI do cech;16 dodatkowych wątków w KAŻDYM procesie byłoby nadsubskrypcją. Pełny port wymaga osobnych zgodnych przejść gier i testów różnicowych,nie tylko kompilującego się API.
