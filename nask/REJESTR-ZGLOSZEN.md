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

## Sesja nocna 03/04.11 (Arena `5ed750ef`, Actions, limiter 4.5 rps, GET-only)

| # | host(y) | hipoteza | klasa | status testu | wynik |
|---|---|---|---|---|---|
| H1 | 12 hostów | ekspozycje plików/endpointów (16 ścieżek, catch-all) | 3/12 | Actions bieg 1 | patrz `noc-20261103/out/report.md` |
| H2 | hosty Next.js | `_next/image` czyta wewnętrzne URL-e (SSRF) | 5.2 | Actions bieg 1 | j.w. |
| H3 | hosty Next.js | `_next/data/<buildId>` bez autoryzacji / draft-mode | 12 | Actions bieg 1 | j.w. |
| H4 | science/116sos | wtyczki WP z publicznym PoC CVE w podatnej wersji | wykl./8 (z PoC dozwolone) | Actions bieg 1 | j.w. |
| H5 | bezpiecznewybory, secure.edu | żywotność + WAF-vs-UA | — | Actions bieg 1 | j.w. |
| H6 | bundle JS T1/T2 | sekrety/endpointy w JS + sourcemapy | 12.2/3 | Actions bieg 1 | `out/jsfindings.md` |
| H7 | wszystkie | AFD cache poisoning (X-Forwarded-Host) | 18 | RĘCZNIE (wymaga 2 żądań z różnymi nagłówkami — po nocnym biegu) | — |
| H8 | wszystkie | cookie sesyjne bez flag = realny scenariusz | wykl. bez scenariusza | pominięte (pułapka regulaminowa) | — |

## Sprawdzone i PUSTE (nie wracać)

| obszar | co testowano | wynik |
|---|---|---|
| 12 domen × 16 ścieżek | `.git`, `.env`, `actuator`, `swagger`, `openapi`, `/api/users` | **zero** — wszystko catch-all SPA (192 żądania, c87 03.11) |
| `nask.pl` | nagłówki, technologia | tylko redirect na www, brak powierzchni |
| `pllum.org.pl` | strona prezentacyjna | statyczna, brak API |

## Stawki przypominacz (§7 pkt 6)

Tier 1: niski 600 / średni 4 000 / wysoki 9 000 / krytyczny 20 000 zł.
Tier 2: 300 / 2 000 / 4 500 / 10 000 zł.
