# PLAN I POMYSŁY — jak realnie zarobić na NASK bug bounty (03.11.2026)

Autor: sesja Smak. Baza: zweryfikowane fakty (patrz `WERYFIKACJA-20261103.md`) + prace
c87/codex. Cel: pieniądze na konto usera w tej edycji (do 30.11), bez ryzyka prawnego.

## 0. Zasady twarde (naruszenie = odrzucenie zgłoszenia / problem prawny)

- TYLKO 12 hostów z listy §5 (sprawdzać każdorazowo; subdomeny NIE wchodzą).
- ≤ **5 req/s** łącznie dla automatów; ręczne klikanie własnym rytmem jest OK.
- Tylko brak auth albo WŁASNE konta testowe; nigdy cudze; bez VPN/kont domenowych.
- DoS/obciążenie zakazane; skaner bez ręcznego potwierdzenia = odrzucone.
- PoC + instrukcja odtworzenia obowiązkowe; dyskrecja do naprawy; zgłoszenie TYLKO
  formularzem platformy; wygrana do potwierdzenia w 7 dni.

## 1. Gdzie są pieniądze (kolejność wg stosunku szansa/praca)

| # | cel (tier) | klasa | dlaczego realne |
|---|---|---|---|
| **P0** | `zglos-dezinformacje.nask.pl` (T1) | **IDOR/BAC na zgłoszeniach** — czy moje zgłoszenie/plik/status można odczytać innym ID? Sekwencyjne ID, /api/report/{id}, brak checku ownera | formularz publiczny, ID pewnie sekwencyjne; BAC to najczęstsza płatna klasa; własne 2 konta testowe wystarczą |
| **P1** | `zglos-dezinformacje.nask.pl` (T1) | **File upload** — gdzie ląduje załącznik? publiczny URL? kontrola typu/nazwy (stored XSS przez PDF/HTML/SVG, path traversal w nazwie, nagłówek Content-Disposition)? | upload wprost obecny w formularzu; „file upload ze skutkiem" jest w regulaminie §8 |
| **P2** | `zglos-dezinformacje.nask.pl` (T1) | **SSRF przez pole URL/źródła dezinformacji** — jeśli serwer podgląda link (meta/preview), podajemy własny endpoint; pełny odczyt = 6k–20k; blind tylko z dowodem DNS | pole URL niemal pewne; test bez dotykania cudzych systemów (własny serwer/dns) |
| **P3** | `dataannotation.pllum.org.pl` (T2) | logowanie/role w HIVE — **jeśli user dostanie konto**: IDOR między adnotacjami, eskalacja roli, mass-assignment przy rejestracji/profilu | T2, ale aplikacja z danymi i rolami; po odmowie konta — wrócić do P0–P2 |
| **P4** | `dyzurnet.pl` (T1) | analogicznie do P0/P1 (przepływ zgłoszeń incydentów + załączniki) | druga aplikacja transakcyjna w T1 |
| **P5** | `dns.pl` (T1) | wyszukiwarka/WHOIS: wstrzyknięcia w parametry zapytań, eksporty, API authz; wyciek danych rejestrantów = dane wrażliwe | rejestr = dużo danych; stack własny (nie CDN-owy) |
| **P6** | `oad.nask.pl` (T1) | middleware/API OAD — authz endpointów publicznych treści | aplikacja Next.js+Envoy |
| **P7** | wszystkie 5 aplikacji | **sesje/tokeny**: przewidywalne tokeny resetu hasła (analiza entropii na WŁASNYCH resetach!), JWT (alg/none/weak secret), sesja nie unieważniana po resecie, cookie bez flag z realnym scenariuszem | przejęcie konta = 4k–9k (T1); entropia mierzalna lokalnie |
| **P8** | `science.nask.pl`, `bezpiecznymiesiac.pl` (T2) | WordPress/Next.js: znane CVE z działającym PoC (jeśli wersja podatna), pluginy, user enum zewn. zkonkretowany | niska szansa, tania robota na końcu |

**Czego NIE robić:** strony statyczne (bezpiecznymiesiac, pllum — tylko konfiguracja=wykluczone),
subdomeny poza listą, DoS/rate-limit tests, skanery bez ręcznej weryfikacji, zgłoszenia
„informacyjne" (brak HSTS itd. = wykluczone).

## 2. Toolkit Rust/Rayon (mój kontrybucja; LOKALNIE = bez limitu 5 req/s)

Limit 5 req/s dotyczy ruchu do celów. Analiza LOKALNA pobranych danych jest wolna od limitu
— i tu wygrywamy sprzętem (5950X 16C/64GB ≫ Actions 2 vCPU ≈ sandbox):

1. **`jsdig`** — pobieramy ręcznie/przy przeglądaniu JS bundle'y 5 aplikacji (przeglądarka
   i tak je ściąga; zapis do cache), potem Rayon-parallel parsowanie: endpointy API, ścieżki,
   klucze/tokeny w kodzie, sourcemapy (`.map` → pełne źródła!), schematy zapytań (GraphQL?),
   komentarze deweloperów. Cel: **mapa ataku zrobiona z publicznych assetów**, przewaga nad
   osobami skanującymi ślepo. (memchr/aho-corasick + rayon; 200 MB JS = sekundy na 5950X.)
2. **`tokentropy`** — zbieramy WŁASNE tokeny resetu hasła/sesji (wiele prób, wiele kont
   testowych), Rust liczy entropię/strukturę czasu (ms-resolution seed? przechwytywalne
   przedziały?) — przewidywalny token = przejęcie konta (4 000–9 000 zł T1).
3. **`diffx`** — pomocnik IDOR: dwie sesje (2 konta testowe), równoległe porównywanie
   odpowiedzi (Rayon po parach endpointów), wyróżnianie różnic w treści/rozmiarach.
4. **reuse**: `naskrecon` (guard zakresu + limiter) jako biblioteka scope; `gen_report.py`
   z gałęzi Arena jako szkielet raportu (format platformy); CVSS 4.0 liczone wg wektora —
   uczciwie, bez pompowania (komisja i tak ocenia).

GitHub Actions: NIE do mocy obliczeniowej (2 vCPU/7 GB — mniej niż sandbox, znacznie mniej
niż 5950X), tylko do: CI narzędzi, nocne pasywne monitorowanie CT (crt.sh) pod kątem NOWYCH
certyfikatów na 12 hostach (zmiany = nowe funkcje do oględzin), archiwizacja logów. Zapytania
do crt.sh nie dotykają celów — legalne bez limitu.

## 3. Podział pracy między sesjami (first-wins działa też wewnątrz zespołu!)

- **JEDEN rejestr prawdy**: `REJESTR-ZGLOSZEN.md` (c87) przenosimy do NASK repo; każda sesja
  wpisuje hipotezy ZANIM zacznie testować; zapis: data-godzina, host, klasa, status
  (hipoteza/test/zgłoszone/odrzucone). Bez wpisu = nie testować (unikamy wewnętrznych duplikatów).
- Podział: **codex = zglos-dezinformacje (P0–P2)** (już zaczął), **c87 = naskrecon + dns.pl (P5)**,
  **Smak (ja) = jsdig/tokentropy/diffx + P3/P4/P7 analiza tokenów + quality control raportów**.
  Wzajemnie się uzupełniamy, każdy zapisuje w rejestrze przed testem.
- Decyzje o WYSŁANIU zgłoszenia: zawsze user (GO), przez konto usera na platformie.

## 4. Działania usera (blokery — tylko Ty to zrobisz)

1. **Załóż konto na hack.cert.pl** (18+, polska rezydencja podatkowa; dane do wypłat) — dziś.
2. Załóż 2–3 **konta testowe** w: zglos-dezinformacje.nask.pl, dyzurnet.pl, science.nask.pl
   (+1 na zapas). Dane: wyłącznie fikcyjne (testowe), nieprawdziwe PII.
3. (gdy będzie dostęp) poproś/oceń konto w dataannotation (HIVE) — jeśli zaproszeniowe i się
   nie da, pomijamy bez żalu (P3 fallback = P4).
4. Podaj mi katalog roboczy na 5950X (Windows/WSL?) i czy Rust toolchain ma być tam
   zainstalowany — wtedy przygotuję build + komendy 1:1.

## 5. Realizm finansowy (uczciwie)

- „Niska" (300–600 zł) przy solidnym rekonesansie aplikacyjnym — osiągalna w tygodniu,
  jeśli cokolwiek w tej klasie istnieje.
- „Średnia" (2 000–4 000 zł) przy IDOR/upload/SSRF — to realny cel tej edycji.
- „Wysoka/krytyczna" (9k–20k) = loteria (RCE na nowoczesnym stosie z WAF-ami).
- 5 programów × sukcesywne rozstrzyganie = kilka strzałów; duplikaty z innymi badaczami
  są największym ryzykiem (platforma świeża = tłok w pierwszym tygodniu → **tempo > perfekcja,
  ale nie kosztem zgodności**).

## 6. Harmonogram

- **Dziś/jutro**: user = konta; ja = jsdig v0 + mapa JS zglos-dezinformacje z codexowej
  sesji; codex = jego sesja 45+45+30 na formularzu; wszystko do rejestru.
- **05–08.11**: P0/P1 testy ręczne (wolne tempo, własne konta), szkice raportów
  (szablon + gen_report), pierwsze zgłoszenia jeśli sygnał.
- **09–20.11**: P4/P5/P6 + tokeny (P7) + raporty; nocne CT watch.
- **21–30.11**: domknięcie, raporty końcowe, dokumentacja (paper-track style writeup
  niepotrzebny tu, ale portfolio tak).

## 7. Kompatybilność z preferencjami sprzętowymi usera

- Rust+Rayon: jsdig/tokentropy/diffx/naskrecon — TAK (lokalnie na 5950X, CPU-bound).
- Python FFI+multiprocessing: tylko tam, gdzie Rust nie ma sensu (gen_report, skrypty
  klejące, analiza JSONL) — pyo3 jeśli potrzebna wysyłka do Rusta.
- Actions: orkiestracja/CI/logs, nie compute.
