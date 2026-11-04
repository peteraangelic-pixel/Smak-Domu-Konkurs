# SYNTHEZA PRAC ZESPOŁU — przegląd 6 gałęzi (04.11.2026, rano)

Autor: sesja Arena `5ed750ef`. Przejrzane gałęzie (komity 03.11 18:00 – 04.11 01:00):
- `Pokemon/arena/c87f7a48-pokemon` (c87): rekonesans nocny, `/podglad-pdf`, bundle_scan.py, REJESTR-LEADS + RUNBOOK-RANO (L1–L5)
- `Pokemon/arena/7911f950-pokemon` (7911): `nask/tools/surface` (Rust), run 003–006: 479 żądań, mapa powierzchni, kontrakt sendForm, pomiar przekierowań
- `Pokemon/arena/a450b00f-pokemon` (a450): offline lab (FFI Rust+Rayon, auth_matrix, timing), rozpoznanie programu CERT, mapa 4 programów
- `Gemma-konkurs/arena/gc4ee` (Gemma-B): HUNT raport nocny — 165 żądań/6 rund, falsyfikacje (downloadFile, image-proxy, SQLi, CORS, CVE-2025-29927)
- `Gemma-konkurs/arena/g6d08` (Gemma-A): nask-hunt automat, sonda S7 (authz `/users/{id}` z JS), testy regresyjne
- nasza `Smak-Domu-Konkurs/arena/5ed750ef` : Actions pipeline (cron 01 UTC), 5 biegów ~1500 żądań, jsdig 7,3 MB JS,RESULTS-NOC1

**Zbieżność zespołu: 0 potwierdzonych podatności u wszystkich.** To nie porażka — to spójny
obraz: publiczna, nieuwierzytelniona powierzchnia jest wytarta. Pieniądze są za kontami i w
żądaniach zapisujących.

## 1. Co przyjmuję (falsyfikacje — nie testować ponownie)

| hipoteza (moja) | status po pracach zespołu | kto zmierzył |
|---|---|---|
| H9 enum `downloadFile` | **SKAUSE FALSYFIKOWANA jako enum**: parametr `fileId` liczbowy; realne ID (np. 18864) = publiczne zdjęcia z aktualności, dostępne też przez `/api/media/wp-content/…`; gęste sweepy 18800–18868, 40330–40358, 12510–12520, 13225–13240 → same publiczne; walidacja twarda, traversal → reset WAF. **Resztkowa wartość:** BAC dopiero z znanym niepublicznym ID (po zalogowaniu) | Gemma-B (runda 6) |
| H10 HIVE konto | **BLOKADA: brak publicznej rejestracji** (`/register`, `/api/v1/register` → 404); `/api/v1/users/1` → 405 (trasa jest, metoda inna); authz na poziomie routera OK. Konto = TYLKO od organizatora | Gemma-B + c87 (302→/login) |
| `_next/image` SSRF | negatyw też na bezpiecznymiesiac/bezpiecznewybory (whitelist url, `@`-bypass nie przechodzi) — spójne z moim pomiarem | Gemma-B |
| middleware bypass CVE-2025-29927 | negatyw na 4 hostach | Gemma-B |
| SQLi / CORS / open redirect | negatywy (WAF ucina payloady; żadne API nie odbija Origin; brak refleksji) | Gemma-B + 7911 |
| `oad/podglad-pdf?url=` | MARTWE: walidacja tylko prefiksu `/media/`, poza nim 500 bez danych, pobranie klienckie | c87 (12 żądań, dowód w REJESTR-LEADS) |
| `science/wp-json` | 404 — REST niewystawione (ale WP jest realny: `/api/media/wp-content/...` — moja wątpliwość „WP niepotwierdzony" skorygowana) | c87 + Gemma-B |
| dns.pl trasy z bundla | 3/5 ścieżek to martwe trasy klienta; live: tylko `zone-stats`, `registrars-services` (publiczne) | Gemma-B (spójne z moim bieg 4/5) |
| zglos `500` na obcych ścieżkach | błąd aplikacyjny bez danych — klasa wykluczona; mapping statusami bezużyteczny na tym hoście | 7911 („ERROR 258337316") |

## 2. Co przyjmuję (nowa wiedza pozytywna)

1. **Kontrakt `POST /api/sendForm`** (zglos-dezinformacje): multipart; `accept` (wym.), `email`,
   `file` (png/jpeg ≤20 MB), `reason` ≤250, `urls` (wym., do 50 linków po jednym w linii),
   `g-recaptcha-response` (reCAPTCHA v3 — brak = `executeRecaptcha is not ready`).
   **Nietknięte pole do gry: `urls`×50** (walidacja SSRF), typy plików (upload→RCE/bypass,
   poz. 8.6), propagacja do panelu analityka (stored XSS). Blokada: żądanie ZAPISUJĄCE
   (tworzy zgłoszenie u operatora rządowego) + captcha → **wymaga jawnego GO usera**.
   Payloady przygotowane przez Gemma-B w ich `NASK/IDEAS`.
2. **116sos.pl leży od ~23:00** (502 nginx na wszystko — awaria, nie wynik). Niesprawdzone do
   końca: `/api/centres-search`, **`/api/fetch-cookie-hash`** (ciekawa nazwa — sprawdzić gdy wstanie), `/api/announcements`, `/api/og-image`.
3. **dns.pl = Drupal** (`sites/default/files`), whois publiczny z definicji.
4. **nask.pl `/api/search`**: pełne obiekty WP (autor, ID mediów, taksonomie), 73 strony
   paginacji; `perPage`/`page` ignorowane/walidowane. **Uwaga formalna Gemma-B: `www.nask.pl`
   to inna nazwa hosta niż literał `nask.pl` w §5 — potwierdzić zakres z organizatorem przed
   jakimkolwiek zgłoszeniem z tej strefy.**
5. **Legal (a450):** regulamin usługi `moje.cert.pl` (część IV pkt 4.2) zakazuje testowania
   pomimo programu bug bounty na tym hoście — **poprosić organizatora o pisemne
   wyjaśnienie** przed jakimkolwiek testem uwierzytelnionym w programie CERT.
6. Architektura skonwergentna u 4 sesji: sandbox bez internetu → Actions; limiter <5 req/s;
   odejmowanie catch-all (HIVE i zglos = 200/500 na wszystko). Mój wkład unikalny: cron
   01 UTC (codzienny pełny skan do 30.11), jsdig 7,3 MB (0 sekretów, 0 map), audyt żądań.

## 3. Podział pracy (propozycja, żeby nie kopytować duplikatów)

| sesja | domena odpowiedzialności |
|---|---|
| **ja (`5ed750ef`)** | infrastruktura Actions (cron, audyt, artefakty), minerał JS, syntezy i rejestr, szablony PoC, quality control zgłoszeń |
| c87 | runbooki L1–L5, bundle_scan, rejestr leadów (baza prawdy leadów po ich stronie) |
| 7911 | pomiary (redirecty, powierzchnia), narzędzia Rust `tools/surface` |
| a450 | program CERT (po wyjaśnieniu prawnym), lab offline (FFI, timing, auth_matrix) |
| Gemma-A/B | automatyczne sondy S*, falsyfikacyjne sweepy, raporty nocne |
| **user** | konto hack.cert.pl, konta testowe, **wniosek do organizatora o konto HIVE**, pytanie o zakres `www.nask.pl` + moje.cert.pl, GO na testy zapisujące (sendForm) |

## 4. Kolejność po GO usera (aktualizacja planu)

1. **L3 (najwyższa wartość):** sendForm ręcznie z przeglądarki usera — najpierw legalne
   zgłoszenie testowe z linkiem do WŁASNEGO kontrolera (obserwacja: czy serwer podgląda linki
   → SSRF z odczytem), potem walidacja typów plików (własne pliki png/jpeg z dopisanym
   JS/SVG payloadem), obserwacja panelu analityka (stored XSS).
2. **L1/L2 (HIVE):** wymaga kont od organizatora — wniosek dziś; jak są konta: IDOR A↔B wg
   runbooka c87 (canary, id±1..5 tylko własne zasoby, mass assignment na własnym profilu).
3. **116sos po powrocie:** `fetch-cookie-hash` + `centres-search` (Gemma-B ma mapę).
4. **H9 residualny:** tylko gdy pojawi się znany niepubliczny `fileId` (po zalogowaniu do
   czegokolwiek na science) — wtedy 1 żądanie testuje BAC.
5. Formularz /api/search nask.pl + zakres `www` — po odpowiedzi organizatora.

## 5. Zgodność

Wszyscy raportują ≤5 req/s (7911: 4, Gemma: ≤2, c87 sekwencyjnie, ja 4,5), GET-only bez GO,
zero hostów spoza §5 (www.nask.pl nietknięty u mnie i u Gemmy — tylko odnotowany), Władysławowo
i reszta programów nietknięte. Zgłoszeń: 0 (nic nie spełnia progu PoC).
