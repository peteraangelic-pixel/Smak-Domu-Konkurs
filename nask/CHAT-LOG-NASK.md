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
