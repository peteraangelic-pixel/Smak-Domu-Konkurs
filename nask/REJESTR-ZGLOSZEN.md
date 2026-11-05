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
| **H9** | science.nask.pl | `/api/downloadFile` — „Invalid file id" → enum id po uploadzie WŁASNEGO pliku | 9.2/3.2 | **FALSYFIKOWANY jako enum** (Gemma-B runda 6: wszystkie 200 = publiczne media z `/api/media/…`; parametr `fileId` liczbowy; sweepy 18800–18868/40330–40358/12510–12520/13225–13240 bez niepublicznych) | resztka: BAC tylko z znanym niepublicznym ID (po zalogowaniu) |
| **H10** | dataannotation | HIVE: FastAPI `/api/v1` + trasy `/admin/logs` (guardy tylko klienta) | 9/10 | **BLOKADA: brak publicznej rejestracji** (`/register`→404); authz routera OK (401); **`/admin/logs` OBALONE przez Gemma-B rundę 7** (= catch-all SPA 713 B, `/api/v1/admin/logs`→404 — mój „guard klienta" był artefaktem pomiaru). Konto TYLKO od organizatora | 4 500–10 000 zł **po kontach** |
| H11 | zglos-dezinformacje | P0–P2 (IDOR/upload/SSRF); **kontrakt znany**: `POST /api/sendForm` (accept/email/file png-jpeg≤20MB/reason≤250/urls×50/reCAPTCHA v3) | 7/9/5 | **GŁÓWNY WEKTOR** — testy walidacji urls (SSRF) i typów plików to żądania ZAPISUJĄCE + captcha → czeka na GO usera; payloady gotowe (Gemma-B `NASK/IDEAS`) | 9 000–20 000 zł |
| H12 | dns.pl | domain-browser/who-is-xml — poznać kształt parametrów z chunków JS | 4/12 | **UŚPIONA**: 3/5 tras z bundla martwe (Gemma-B); live tylko publiczne zone-stats/registrars-services; dns.pl = Drupal | 4 000–9 000 zł (wymaga nowej mapy z chunków) |
| H13 | dyzurnet.pl | `/api` (robots) — mapa z chunków | 9/12 | OTWARTA (nikt nie zmapował; media `/media/…` publiczne) | 4 000–9 000 zł |
| **H14** | 116sos.pl | `fetch-cookie-hash`, `centres-search`, `announcements`, `og-image` | 9/12 | **DOMKNIĘTE** (Gemma-B runda 7, host wrócił): cookie-hash = stała 30 B (nie pochodna sesji, XFH bez wpływu); centres-search **ignoruje q/id** — zwraca publiczną listę ośrodków (13,3 kB) | 0 |
| **H15** | oad.nask.pl | `/podglad-pdf?url=` SSRF/LFI | 5/15 | **MARTWE** (c87: prefiks `/media/` walidowany, poza nim 500 bez danych) | 0 — nie wracać |
| **H16** | nask.pl (www?) | `/api/search` — obiekty WP, 73 strony | 3/12 | obserwowane (Gemma-B); **pułapka zakresu: `www.nask.pl` ≠ literał `nask.pl`** — najpierw pytanie do organizatora | ? |
| **H17** | hack.cert.pl (program CERT) | **IDOR H1–H7** na `/api/v1` (cudze `reports/{id}`, `internal-notes`, `attachments/…/download`, `reward-offers` stany, `users/{uid}/role`) — pełna mapa w `kit/19` (16-MAPA-ENDPOINTOW) | 3/9/12 | **OTWARTA — czeka konto + własne zgłoszenie testowe** (najpierw format ID!); pojedyncze żądania, zero zrzutów | 9 000–20 000 zł |
| **H18** | mSzyfr (komunikator.narodowy.gov.pl) | Element/Matrix: IDOR rozmów (2 WŁASNE konta), ATO resetem, join po room-id/alias, invite-linki | 2/3/9 | OTWARTA — czeka 2 konta; bundle tylko z przeglądarki (catch-all 200); auth: `mas.komunikator…` | 9 000–20 000 zł |
| **H19** | n6portal.cert.pl (CERT) | `/org_config` vs zwykły user, MFA-confirm bez MFA, `/api_key` po ID, `sources` | 9/12 | OTWARTA — czeka konto (mapa z bundla w `kit/19`, dodatek 2) | 4 000–9 000 zł |
| **H20** | oad.nask.pl | PowerBI embed `autoAuth=true` — co pokazuje publiczny raport (pasywne oględziny) | 3 | OTWARTA (przeglądarka usera; prawdopodobnie agregaty = zero) | 0–4 000 zł |
| **H21** | hack.cert.pl | awatar SVG (stored XSS) — instrukcja Gemmy, 15 min po koncie | 8 | OTWARTA | 600–4 000 zł |
| **H22** | mwdb.cert.pl | XSS Rich attributes (#1272/#1274) | 8 | **ZAMKNIĘTA** — produkcja 2.20.0, poprawka wdrożona (Gemma-A 04.11, sonda S8) | 0 |

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

## Hipotezy nocnego operatora (Drive 20/22, 04–05.11) — status po moich pomiarach

| id | host | hipoteza | klasa | status |
|---|---|---|---|---|
| D1/D2 | dns.pl | POST `/api/who-is-xml/{loc}`/`/api/domain-browser/{loc}` bez captcha → dane > publiczny whois | 3.3/12.2 | **NIEOSIĄGALNE skryptem** (bieg 7: 3 POST-y = catch-all HTML 51 kB; SPA dodaje sesję/CSRF) → **test z DevTools usera: Replay z pustym captcha, porównać pola z whois www** |
| D3 | dns.pl | registrars-list sort/order SQLi | 9.2 | do usera (kontekst SPA) |
| — | dns.pl | XFH→`<script src>` + shared cache = poisoning poz.18 | 18 | **NIEPOTWIERDZONE** (bieg 7: 6 ścieżek, 0 odbić w oknie 400 B; operator: brak cache na /) — wątek zamknięty |
| — | bezpiecznapoczta.cert.pl | /check-domain/scan → SSRF przez własną domenę A→127.0.0.1 | 5 | **CZEKA NA DOMENĘ USERA** (program CERT; nikt o tym hoście nie pamięta — najczystszy punkt SSRF zakresu) |
| — | mas.komunikator.narodowy.gov.pl | DCR `/oauth2/registration` aktywny → klient OAuth z naszym redirect_uri = ATO 20k | 2 | **NAJWYŻSZY PRIORYTET po GO** (wymaga POST + domena usera; rejestracja zamknięta, ale DCR żyje) |
| — | m.cert.pl | Mattermost 11.7.14 — cel #1 gdy będzie konto gościnne | 9 | czeka konto |
| L14 | bezpiecznymiesiac.pl/ecsm/zglos-inicjatywe/ | ta sama klasa co sendForm, mniejsza konkurencja | 7/13/8 | czeka GO |
| L23 | zglos-dezinformacje | sendForm **bez tworzenia rekordu** (brak accept/puste urls/zero captcha) | 7/13 | czeka jawne GO; UWAGA: 22-RAPORT mierzył 403 bez tokenu reCAPTCHA + Zod 422 = walidacja dobrze zbudowana → L23 pewnie zamknie się negatywnie |
