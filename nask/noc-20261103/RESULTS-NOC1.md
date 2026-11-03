# WYNIKI NOCNEJ ZMIANY 03/04.11.2026 (sesja Arena `5ed750ef`) — program NASK, hack.cert.pl

Wykonawca: GitHub Actions (ubuntu-latest, pełny internet — sandbox nie dosięga celów).
Narzędzia: `nightscan.py` + `bieg2..5.py` (stdlib, sekwencyjne, globalny limiter **4,5 req/s**,
guard dokładnych hostów §5, GET-only, zero auth, zero zapisów, pełny audyt: `out/requests.jsonl`).
5 biegów, łącznie **~1500 żądań**, wszystkie ≤4,5 rps (regulamin: ≤5). Władysławowo: nietknięte.
Poza zakresem (subdomeny, zaplecza): nietknięte. DoS/obciążenie: nie było.

## 1. Najważniejszy wynik nocny: MAPA API i kandydaci

| # | host | odkrycie | klasa (§8) | następny krok | potencjał |
|---|---|---|---|---|---|
| **H9** | `science.nask.pl` (T2) | **`/api/downloadFile` istnieje** — `{"error":"Invalid file id"}`; bez parametru zwisa >15 s (długotrwała operacja) | 9.2/3.2 BAC | poznać format `file id` (id? hash?), sprawdzić enum **na jednym własnym pliku** (upload przez CMS po zalogowaniu) | 2 000–4 500 zł |
| **H10** | `dataannotation.pllum.org.pl` (T2) | backend **FastAPI** na `/api/v1` (401 na `/api/v1/users/`, JSON 404 wprost z backendu); SPA (TanStack) zna trasy `/admin`, `/admin/logs` (guardy klienta), `file-upload` | 9/10 IDOR/uprawnienia | konto → IDOR między kontami, `/api/v1/admin/*` authz, mass-assignment | 4 500–10 000 zł |
| H11 | `zglos-dezinformacje.nask.pl` (T1) | Next.js **App Router** (`__next_error__` 500 na nieznanych ścieżkach — brzydkie, ale bez wpływu); reCAPTCHA na formularzu; 13 chunków JS do dokładnego minera (w nocnych 6 z 6 nie było `/api/…` — logika w flight-data/chunks lazy) | 7/9/5 | konto → upload/IDOR/SSRF (plan P0–P2 bez zmian) | 9 000–20 000 zł |
| H12 | `dns.pl` (T1) | publiczne API JSON: `/api/zone-stats`, `/api/registrars-services` (dane publiczne — NIE są błędem); trasy z JS: `/api/domain-browser/`, `/api/who-is-xml/`, `/api/stats/`, `/api/registrars-list/`, `/api/funny-name/` → 404 bez właściwego parametru/prefiksu; sesje `SESID` 26 znaków base36 (~126 bitów, OK) | 4/12 | z chunków JS dns.pl wyciągnąć wywołania domain-browser (routing po parametrze) | 4 000–9 000 zł (dane abonentów) |
| H13 | `dyzurnet.pl` (T1) | `/api/` w robots → 308 → `/api` → 404 App-Router; API koncepcyjnie jest, trzeba mapy z chunków | 9/12 | chunki JS dyzurnet → trasy fetch | 4 000–9 000 zł |

## 2. Wyniki UJEMNE (nie wracać — oszczędność czasu)

- **`_next/image` SSRF**: zamknięte wszędzie (WAF Azure 403 na samą ścieżkę na zglos/oad/dataannotation/pllum; poprawne `url parameter is not allowed` na nask.pl/science/bezpiecznymiesiac; dyzurnet 404; dns.pl to nie Next).
- **Ekspozycje statyczne** (192 żądania, 2 biegi): zero. Wszystko catch-all/WAF.
- **X-Forwarded-Host refleksja** na 5 hostach Azure: brak refleksji w treści.
- **`/api/search` (science)**: błędy walidacji JSON, brak refleksji przy płytkich próbach; SQLi/XSS — dopiero głębsze testy z kontrolowanymi odpowiedziami (a do tego trzeba rozumieć klienta).
- **sourcemapy**: żaden z 47 bundle'ów nie wystawia `.map` (0 prób URL-i map — brak komentarzy sourceMappingURL).
- `bezpiecznewybory.pl`: 403 „Access Denied" także dla UA przeglądarki z IP Actions — testowalne tylko z domu usera. `secure.edu.pl`: martwy z Actions (timeout) — sprawdzić z Polski.
- `nask.pl`: 302→`www.nask.pl` (poza dosłownym scope — nie testujemy www bez jasnej interpretacji), klucz reCAPTCHA w NEXT_PUBLIC = **jawny, nie zgłaszać**.

## 3. Fakty architektoniczne (przydadzą się przy każdym zgłoszeniu)

- Stack: Azure Front Door + Envoy (zglos, oad, dataannotation, pllum, bezpiecznymiesiac; cache `CONFIG_NOCACHE`), Cloudflare (dyzurnet), własny stack z SESID (dns.pl), Next.js pages-router z `__NEXT_DATA__` (116sos, science; buildId: `8CjJwbyxpVqpWnorny23T`, `Grl_YQ5SCHd1ahmhesPv6`), Next.js app-router (zglos-dezinformacje, dyzurnet).
- HIVE (dataannotation): SPA Vite+React+TanStack, API `https://dataannotation.pllum.org.pl/api/v1`, FastAPI (`{"detail":"Not Found"}`).
- Kontakt IOD w strukturach: `iod@nask.pl`; monitoring: Application Insights (polandcentral).
- WP nie potwierdzony (0 wzmianek wp-content w głównych HTML — rekonesans c87 „Next.js+WordPress" wymaga ponownego sprawdzenia pod inną ścieżką).

## 4. Co dalej (rano, po GO usera i założeniu kont)

1. **User: konto platformy + konta testowe** (zglos-dezinformacje, dyzurnet, science) — bez tego klasy płatne (IDOR/BAC/upload/SSRF) są nieosiągalne.
2. Z kontem: H9 (science downloadFile — po uploadzie WŁASNEGO pliku poznać format id i testować dostępność), H10 (HIVE IDOR/authz), H11 (P0–P2).
3. Minerał głębszy: zglos-dezinformacje flight-data (13+ chunków), dyzurnet chunki, dns.pl chunk z domain-browser.
4. Cron 01:00 UTC biegnie pełny skan co noc; push uruchamia tylko biegi celowane (zmiana w workflow).
5. Każdą hipotezę przed testem wpisujemy do `nask/REJESTR-ZGLOSZEN.md` (first-wins też wewnątrz zespołu).

## 5. Zgodność (audyt)

- Wszystkie żądania: `out/requests.jsonl` (pełna lista, sekunda po sekundzie, z modułem i odpowiedzią).
- 5 biegów Actions: runy 41733874404, 41734624746, 41735809114, 41736780974, 41737652101.
- Zero żądań poza 12 hostami §5 (guard w kodzie odmawia wysyłki), zero metod poza GET, zero auth, zero prób obejścia limitów.
