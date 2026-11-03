# Rejestr zgłoszeń — NASK Bug Bounty 11/2026 (kopia robocza sesji Arena `5ed750ef`)

Uzupełniaj na bieżąco. Ten plik jest jedynym miejscem, gdzie wiadomo, co już zgłoszone
(duplikat = zero nagrody, §7 pkt 8). Bazowy szablon: `nask/kit/zipped/.../REJESTR-ZGLOSZEN.md`.
Reguła zespołu: **hipotezę wpisujesz PRZED testowaniem**; first-wins obowiązuje też wewnątrz zespołu.

## Zgłoszenia wysłane

| # | data | domena | klasa (§8) | CVSS 4.0 | tier | oczekiwana kwota | status | ref |
|---|---|---|---:|---:|---:|---:|---|---|
| — | — | — | — | — | — | — | jeszcze nic nie wysłano | — |

## Kandydaci w toku

| domena | co sprawdzamy | klasa | zmierzony wynik | następny krok |
|---|---|---|---|---|
| `dataannotation.pllum.org.pl` | dostęp do cudzych zadań po ID | 9.2 IDOR | — | dwa konta, mapa endpointów |
| `zglos-dezinformacje.nask.pl` | walidacja uploadu | 7 | — | przepływ zgłoszenia z załącznikiem |
| `zglos-dezinformacje.nask.pl` | pobieranie linku przez serwer | 5 SSRF | — | pole „źródło" + własny endpoint |
| `oad.nask.pl` | ominięcie middleware Next.js | 9/12 | test w `naskrecon hypotheses` | sprawdzić wersję Next.js |
| `dns.pl` | odczyt danych abonenta domeny | 3.1 | — | wyszukiwarka whois |

## Sesja nocna 03/04.11 (Arena `5ed750ef`, Actions, limiter 4.5 rps, GET-only, ~1500 żądań, audyt: noc-20261103/out/requests.jsonl)

| # | host(y) | hipoteza | klasa | status testu | wynik |
|---|---|---|---|---|---|
| H1 | 12 hostów | ekspozycje plików/endpointów (16 ścieżek, catch-all) | 3/12 | **ZMIERZONE ×2** | **PUSTE** — zero ekspozycji, wszystko catch-all/WAF |
| H2 | hosty Next.js | `_next/image` czyta wewnętrzne URL-e (SSRF) | 5.2 | **ZMIERZONE** | **ZAMKNIĘTE** — WAF 403 lub poprawna odmowa wszędzie |
| H3 | hosty Next.js | `_next/data/<buildId>` bez autoryzacji | 12 | częściowo (buildId poznane późno) | brak sygnału; dokończyć na 116sos/science |
| H4 | science/116sos | wtyczki WP z publicznym PoC | wykl./8 | **ZMIERZONE** | **brak WP w HTML/JS** — rekonesans c87 do weryfikacji; nie potwierdzony |
| H5 | bezpiecznewybory, secure.edu | żywotność + WAF-vs-UA | — | **ZMIERZONE** | bezpiecznewybory: 403 dla wszystkich UA z IP Actions; secure.edu: martwy z Actions — test z domu |
| H6 | bundle JS T1/T2 | sekrety/endpointy w JS | 12.2/3 | **ZMIERZONE** | 47 bundle'ów/7,3 MB: **0 sekretów**, 0 map; natomiast MAPA API (H9–H13) |
| H7 | 5 hostów Azure | XFH refleksja → cache poisoning | 18 | **ZMIERZONE** | brak refleksji — odłożone do ręcznego testu z przeglądarki |
| H8 | wszystkie | cookie bez flag z realnym scenariuszem | wykl. | świadomie pominięte | pułapka regulaminowa |
| **H9** | science.nask.pl | `/api/downloadFile` — „Invalid file id" → enum id po uploadzie WŁASNEGO pliku | 9.2/3.2 | **OTWARTA** (kontrakt potwierdzony) | 2 000–4 500 zł |
| **H10** | dataannotation | HIVE: FastAPI `/api/v1` + trasy `/admin/logs` (guardy tylko klienta) | 9/10 | **OTWARTA** (czeka konto) | 4 500–10 000 zł |
| H11 | zglos-dezinformacje | P0–P2 (IDOR/upload/SSRF) | 7/9/5 | OTWARTA (czeka konto) | 9 000–20 000 zł |
| H12 | dns.pl | domain-browser/who-is-xml — poznać kształt parametrów z chunków JS | 4/12 | OTWARTA | 4 000–9 000 zł |
| H13 | dyzurnet.pl | `/api` (robots) — mapa z chunków | 9/12 | OTWARTA | 4 000–9 000 zł |

Szczegóły: `noc-20261103/RESULTS-NOC1.md`.

## Sprawdzone i PUSTE (nie wracać)

| obszar | co testowano | wynik |
|---|---|---|
| 12 domen × 16 ścieżek | `.git`, `.env`, `actuator`, `swagger`, `openapi`, `/api/users` | **zero** — wszystko catch-all SPA (192 żądania, c87 03.11) |
| `nask.pl` | nagłówki, technologia | tylko redirect na www, brak powierzchni |
| `pllum.org.pl` | strona prezentacyjna | statyczna, brak API |

## Stawki przypominacz (§7 pkt 6)

Tier 1: niski 600 / średni 4 000 / wysoki 9 000 / krytyczny 20 000 zł.
Tier 2: 300 / 2 000 / 4 500 / 10 000 zł.
