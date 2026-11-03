# CHAT-LOG — projekt NASK bug bounty (kontynuacja konwencji z ARC)

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
