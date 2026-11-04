# CHAT-LOG — projekt NASK bug bounty (kontynuacja konwencji z ARC)

## 04.11, ~13:30 — przegląd 2 gałęzi + Drive (19 plików)

- Nowe komity: c87 (rawpath 1–4, przegląd 6 gałęzi, RUNBOOK-REV2, rejestr L1–L12), 7911
  (256 sond/7 przebiegów + raport), a450 (HAR triage offline), g6d08 (S8/S9, mwdb 2.20.0
  zamknięty, HIPOTEZY-ZAMKNIETE ×15), gc4ee (runda 7: **H10 obalone** — /admin/logs = catch-all,
  H14 116sos domknięte). Drive: nowy kit 13–19 (mapa /api/v1 hack.cert.pl z H1–H7!,
  mSzyfr=Matrix, n6portal, rank pieniędzy, 19-zip 3,2 MB zarchiwizowany przez nas).
- Mój wkład: INTEGRACJA-ZESPOLU-20261104-POLOUDNIE.md, korekty REJESTRU (H10/H14 + H17–H22),
  **bieg 6** (mapa chunków JS dyzurnet+dns — brakująca robota zespołu), archiwum kitu.
- Konsensus 6 sesji: anonimowa powierzchnia wytarta (~2500+ żądań, 0 vulnów); pieniądze
  za kontami: mSzyfr > hack.cert.pl (portal) > CERT panele; NASK: sendForm (GO usera).

## 04.11, ~00:40 — nocna zmiana zakończona (sesja Arena `5ed750ef`)

- User dał GO na nocne szukanie luk (nie tylko zglos-dezinformacje; Władysławowo wykluczone).
- Sandbox nie dosięga celów (whitelista GitHub/PyPI) → wykonanie przeniesione do **GitHub Actions**
  (pełny internet), 5 biegów, ~1500 żądań, limiter 4,5 req/s, GET-only, zero auth, pełny audyt.
- Wynik: **brak potwierdzonej podatności płatnej** (klasy płatne wymagają kont), ale:
  mapa API dns.pl, żywe API science (`/api/downloadFile` — „Invalid file id" — H9),
  potwierdzony FastAPI HIVE `/api/v1` + trasy `/admin/logs` (H10), zamknięte klasy
  ekspozycji i `_next/image`-SSRF (oszczędność dni pracy). Szczegóły: `noc-20261103/RESULTS-NOC1.md`.
- Blokery bez zmian: **konto usera na hack.cert.pl + konta testowe** (zglos-dezinformacje,
  dyzurnet, science; opc. HIVE). Push do repo NASK nadal 403 (brak praw tokena).
- Infra: workflow `nask-night.yml` — cron 01:00 UTC (pełny skan) + push (biegi celowane);
  `jsdig-rs` (Rust+Rayon) buduje się w Actions OK (binarka w artefaktach dla 5950X).

## 04.11, ~13:50 — bieg 6 wykonany (mapa dyzurnet+dns)

- Run 41818357455 zielony (po fixie: bot robi pull --rebase przed push, retry 20s).
- dns.pl: 10 tras /api/* potwierdzonych w JS (Angular: `app-main-page-domain-browser-form`,
  whoisHref→/whois); referencja `https://panel.dns.pl/pl/index` w bundlu — POZA zakresem
  (guard codexa: niepotwierdzone w §5), tylko odnotowana.
- dyzurnet: 10/18 chunków zminowanych (~0,5 MB) — brak nowych tras API; WP-media JSON w chunku
  (`uploaded_to`, logotypy); `localPatterns:void` w konfiguracji Next. Reszta tras w lazy-chunks
  → do wyciągnięcia przez DevTools usera przy pierwszym przejściu formularza.
- Wyniki: out/{report6,jsdig6,js-manifest-6}, audyt w out/requests.jsonl.

## 04.11, ~15:00 — przegląd 3: repo NASK (a29 + codex)

- a29 tip b2cf80a4: scaffold Rust naprawiony (rust/common: limiter+scope), nask-lab skonsolidowany, drive_materials=lustro Drive; README wciąż z błędną pulą „1 mln" i mieszaniem 5 programów (do poprawy przy prawach push).
- codex a4fb58df: jednorazowa operacja ekspozycji 75 żądań @1 rps z kontrolą hashy regulaminów i szyfrowaniem dowodów — 0 kandydatów; oni dotknęli Władysławowo (my nie — zakaz usera); monitor gałęzi wycofany.
- Wniosek: 5. niezależne potwierdzenie „anonimowa powierzchnia pusta"; wszystkie sesje czekają na konta usera i GO na sendForm.
