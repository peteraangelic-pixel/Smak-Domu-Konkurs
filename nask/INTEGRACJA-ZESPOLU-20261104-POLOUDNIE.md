# INTEGRACJA ZESPOŁU — przegląd 2 (04.11, południe; gałęzie + Drive 19 plików)

Autor: sesja Arena `5ed750ef`. Źródła: nowe komity 5 gałęzi (c87 ×8, 7911 ×7, a450 ×2,
g6d08 ×5, gc4ee ×3) + Drive 13–19 (w tym 16-MAPA-ENDPOINTOW 9,7 kB i zip 19 — zarchiwizowane
w `nask/kit/`). Poprzednia synteza: `SYNTEZA-ZESPOLU-20261104.md`.

## 1. Korekty mojego rejestru (przyjęte z dowodami)

| pozycja | co się zmieniło | kto/źródło |
|---|---|---|
| **H10** | `/admin/logs` = **catch-all SPA 713 B**, `/api/v1/admin/logs`→404 → mój „guard tylko klienta" był **artefaktem pomiaru**. HIVE pozostaje otwarte WYŁĄCZNIE jako IDOR po kontach od organizatora | Gemma-B, runda 7 (`WERYFIKACJA-RUNDA7`) |
| **H14** (116sos) | **DOMKNIĘTE**: `fetch-cookie-hash` = stała 30 B (nie pochodna sesji); `centres-search` ignoruje q/id = publiczna lista ośrodków | Gemma-B, runda 7 |
| H9 resztki | `download-file` (bezpiecznymiesiac): normalizacja prefiksu, kropki odrzucane w każdym kodowaniu — klasa 8.15 zamknięta | Gemma-B + 7911 (20 wariantów) |
| — | pllum Nuxt drafts = `[]`; Drupal `?_format=json` / WP `?rest_route=` / Next `/_next/data` → 0; Wagtail `/api/v2` → 0 | 7911 (256 sond, 7 przebiegów) |
| **H22** (nowa, zamknięta) | mwdb.cert.pl: sonda S8 `server_version` = **2.20.0** → poprawka XSS #1272/#1274 wdrożona; temat martwy bez zakładania konta | Gemma-A, przebieg 4 |

**Kanoniczny rejestr zamkniętych hipotez** (15 wpisów z dowodami): Gemma-A
`nask/HIPOTEZY-ZAMKNIETE.md` (gałąź `6d081d52`). Zasada: wpis tylko z zakresem testu +
surowym wynikiem + ścieżką dowodu. My trzymamy zgodny H1–H22 w `REJESTR-ZGLOSZEN.md`.

## 2. Najważniejsze NOWE źródło: mapa hack.cert.pl `/api/v1` (kit Drive 16)

Portal konkursu jest w zakresie programu CERT (`*.cert.pl`, T1) i **ma komplet endpointów
wypisany w bundlu** (index-B5IFYBO_.js). Kluczowe: rozdział `reports/{id}` (staff) vs
`me/reports/{id}` (uczestnik); `internal-notes`, `attachments/{aid}/download`,
`reward-offers` + akceptacje, `users/{uid}/role|email`, `institutions/.../editions/...`
(activate/suspend/payout-export). **Hipotezy H1–H7 z warunkami odrzucenia** — do testu
pojedynczymi żądaniami PO zalogowaniu (najpierw poznać format ID we własnym zgłoszeniu).
Anonimowy wariant (S7 Gemmy) zamknięty: żadna trasa nie odpowiada 2xx bez tokenu.

Pozostałe mapy z kitu: **mSzyfr = Element Web/Matrix** (auth `mas.komunikator.narodowy.gov.pl`;
bundle tylko z przeglądarki; plan 2 własnych kont: IDOR rozmów/ATO/room-id), **n6portal**
(OIDC/MFA/api_key/incidents), moje.cert.pl (Django, nisko), oad (PowerBI embed `autoAuth=true`
— pasywne oględziny co pokazuje).

## 3. Rank pieniędzy (konsensus zespołu, Drive 17 + runbooki)

1. **mSzyfr** — komunikator = cudze rozmowy (IDOR/ATO); 2 własne konta; 9–20k.
2. **hack.cert.pl** (portal) — najmłodszy kod; H1–H7 po koncie; 9–20k (+H21 awatar SVG 15 min).
3. CERT panele (moje/n6/mwdb) — mwdb zamknięty; moje+n6 po kontach; 4–9k.
4. NASK reszta: sendForm (L1 runbooka rev2, wymaga GO), dyzurnet/dns mapy (MOJE, bieg 6), HIVE po kontach.
5. gov.pl — nisko; Władysławowo — pomijamy.
**Kalibracja:** 1–2 trafienia 4–9k/mies. realne; 20k = łańcuchy (RCE/ATO/SSRF z odczytem).
Uwaga: **3 odrzucone zgłoszenia z rzędu mogą zablokować konto** (Gemma-B IDEAS §0) → wysyłamy
tylko z działającym PoC.

## 4. Pulapki/prawne (zaktualizowane)

- `panel.dns.pl` / `partner.dns.pl` — niepotwierdzone w zakresie, **nie dotykać** (Drive 17).
- `incydent.cert.pl` — **bez fikcyjnych zgłoszeń testowych**.
- `info-trace.116sos.pl` (z nagłówka ACAO) i `www.nask.pl` — dopytać organizatora o zakres (c87 L0.3).
- Program CERT: regulamin *usługi* moje.cert.pl IV §4.2 vs program — najpierw pisemne wyjaśnienie (a450).
- Kliknięcia/nagłówki/CORS-* bez credentials — wszystkie odrzucone przez §8 (Drive 14: 19 findingów, 0 przyjętych — poprawny triage).

## 5. Mój wkład w tej turze

- **Archiwizacja kitu Drive** (13–18 + zip 19, 3,2 MB) → `nask/kit/`.
- **Bieg 6**: mapa chunków JS `dyzurnet.pl` + `dns.pl` (to, co cały zespół odłożył) —
  Actions, GET-only publiczne assety, digest z kontekstem → `out/jsdig6.json` + `report6.md`
  → zasilia H12/H13.
- Korekty rejestru (powyżej) + ta integracja.

## 6. Checklista usera (L0 z runbooka rev2 c87 + priorytety)

1. Konto **hack.cert.pl** + akceptacja regulaminów (NASK i platformy).
2. Wniosek o **konto testowe HIVE** (dowód braku rejestracji: 2 niezależne pomiary).
3. Pytania o zakres: `www.nask.pl`, `info-trace.116sos.pl`; pisemnie o moje.cert.pl (program CERT).
4. Konta własne: **mSzyfr ×2**, moje.cert.pl (opc. mwdb — już niepotrzebne do H22).
5. Po koncie hack.cert.pl: **awatar SVG** (H21), format ID własnego zgłoszenia (klucz do H17),
   potem H1–H7 wg mapy (pojedyncze żądania!).
6. **GO na sendForm** (L1 rev2: kroki 1.1–1.5) — jedyna żywa ścieżka na 9k w programie NASK.

## 7. Dodatek — przegląd 3 (04.11, po południu): repo `peteraangelic-pixel/NASK`

| gałąź | co nowego (dowód: komity) | wpływ na nas |
|---|---|---|
| `arena/a29ca234-nask` (tip `b2cf80a4`, 4 komity) | **scaffold Rust NAPRAWIONY**: nowy wspólny crate `rust/common` (`rate_limit.rs` + `scope.rs`), poprawione Cargo/main `subenum/ffuzz/probe/native` (komit `10cbb620`); **`nask-lab/`** = konsolidacja naskhunt+nasktriage (analyze/har/rate; komit `eb234af8`); `drive_materials/` 00–18 (komity `3f3bc29b`,`b2cf80a4`) — lustrzana kopia Drive 00–18 (my: `nask/kit/`) | narzędzia zespołu są teraz jedną działającą całością w repo NASK; my trzymamy własny nightscan/jsdig — brak potrzeby kopiowania |
| `arena/a29ca234-nask` README | **wciąż stare błędy**: „pula 1 mln PLN", „scope = 5 programów w jednym arkuszu" — c87 korygował w PRZEGLĄDzie | poprawić przy pierwszym pushu do NASK (nasz token bez praw — 403) |
| `codex/multi-program-lab-20261103` (tip `a4fb58df`, 3 komity) | jednorazowa operacja ekspozycji [lab-night]: **75 żądań, 1 req/s, 0 kandydatów, 0 podatności** (run 41734282345, `completed_with_skips`); **kontrola hashy regulaminów przed startem** (niezgodność = stop), stop na 429/403/5xx, limit 64 KiB odczytu, **dowody szyfrowane** (klucz lokalny, w repo tylko podsumowanie+receipt); mSzyfr i CTF nadal odłożone; **testowali też Władysławowo (4 hosty) — my NIE, zgodnie z Twoim zakazem** | wynik spójny z resztą zespołu; monitor gałęzi wycofany |
| lekcja metodologiczna | kontrola hashy regulaminów PRZED skanem = wykrywa zmianę edycji/regulaminu automatycznie | do rozważenia jako lekkie wzmocnienie naszego crona (biegi i tak GET-only) |
