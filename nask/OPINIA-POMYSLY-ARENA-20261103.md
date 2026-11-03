# OPINIA + POMYSŁY DOŁĄCZAJĄCE — sesja Arena `5ed750ef` (03.11.2026, wieczór)

Autor: druga sesja Smak na tej gałęzi. Kolega (równoległa sesja Smak) zrobił już
`WERYFIKACJA` + `PLAN-I-POMYSLY` (P0–P8, toolkit jsdig/tokentropy/diffx, podział pracy).
Nie duplikuję — **dokładam brakujące klasy ataków i decyzje operacyjne**. Bazuję na:
własnym odczycie stron programów (NASK + mSzyfr, dziś), regulaminie wprost z
hack.cert.pl, rekonesansie c87, przeglądzie repo NASK i kitu z Drive (3.11, 18:35).

## 0. Stan (zweryfikowany dziś przeze mnie)

- **Pokemon a450**: brak nowych komitów od 30.10 (d077ee9) — pakiet `nask/` (strategia,
  naskrecon, rejestr) to ich najnowszy wkład; Drive ma świeższy komplet (18:35).
- **NASK repo**: `main` = sam README; `arena/a29ca234-nask` = scaffold (25 plików, ale
  3/4 crate'ów się nie buduje — potwierdza przegląd kolegi); `codex/multi-program-lab`
  = 58 plików (recon Rust+FFI, evidence, testy, verified Actions pilot).
- **Drive**: 15 plików = kompletny kit (00–12 + 3 wersje zipu); najnowszy 08 (18:35)
  zarchiwizowany przez nas w `nask/kit/`.
- Program NASK: **3–30.11**, T1 `nask.pl, dyzurnet.pl, dns.pl, oad.nask.pl,
  zglos-dezinformacje.nask.pl` (600/4k/9k/20k), T2 siedem hostów (300/2k/4,5k/10k),
  ≤5 req/s, własne konta, PoC obowiązkowe, first-wins, sukcesywne rozstrzyganie.

## 1. Moje dodatkowe klasy ataków (czego brakuje w PLAN-I-POMYSLY)

### A. Next.js: `_next/image` jako SSRF-as-a-feature (poz. 5.2)
Cała Tier-1 aplikacja i trzy Tier-2 stoją na Next.js. Optymalizator `/_next/image?url=…`
pobiera zdalny obraz na żądanie serwera. Jeśli `images.domains/remotePatterns` jest
błędnie skonfigurowany (albo pozwala wildcard), URL wewnętrznego zasobu (np.
`http://169.254.169.254/…`, `http://envoy:port/…`) zwraca **treść** w odpowiedzi
(serwer pobiera i zwraca bufor obrazka) → **odczyt usług prywatnych = poz. 5.2, wysoka
(9 000 zł T1)**. Tanie w teście: kilka żądań z własnym URL-iem. Analogicznie:
`_next/data/<buildId>/…` — **buildId wycieka z HTML** i bywa wrażliwy na BAC na
 маршрутach JSON (poz. 12).

### B. `__NEXT_DATA__` i propsy SSR: wycieki wewnętrznych struktur (poz. 3.2/12.2)
Rekonesans c87 potwierdził `__NEXT_DATA__` na 5 aplikacjach. Audyt tego JSON-a
(lokalnie, bez limitów) często pokazuje: wewnętrzne ID, role, pola API, czasem
tokeny preview/draft (Next.js Draft Mode!) i **prefetchowane cudze rekordy**.
Lokalne Rust/Python parsowanie + diff między rolami = materyał do IDOR-ów.

### C. Azure Front Door + cache: Web Cache Poisoning (poz. 18)
Wszędzie `x-cache`/`x-cache-info` (AFD). Klasyczny test: manipulacja
`X-Forwarded-Host`/nagłówkami pochodzenia, które trafiają do klucza cache, przy
odpowiedziach z `Vary`-bałaganem; sukces = serwowanie naszej treści innym
użytkownikom. Wysoka nagroda (9k), test tani (kilkanaście żądań, ręcznie).

### D. WordPress z działającym PoC = dozwolone (poz. wykluczeń: „znane CVE **bez**
działającego PoC")
`science.nask.pl` i `116sos.pl` = Next.js + **WordPress** (rekonesans). Droga:
fingerprint wtyczek z assetów (`/wp-content/plugins/<slug>/…` — publiczne pliki,
zero ataku), krzyżowe z publicznymi CVE **z PoC**, ręczne potwierdzenie na własnym
koncie. To najszybsza droga do pierwszych 600–4 000 zł (T2), mało kontrowersyjna
i nie wymagająca kont (jeśli luka jest przed autoryzacją). NIE zgłaszamy samego
„przestarzałego WP" — tylko działający exploit konkretnej wtyczki.

### E. dns.pl: dwie konkretne rzeczy (P5 doprecyzowanie)
1. **Parametry wyszukiwarki domen**: IDN/punycode, znaki specjalne, eksport —
   klasyczne wstrzyknięcia refleksowane (XSS w wynikach = tylko z wpływem).
2. **RDAP/WHOIS**: dane rejestrantów — jeśli wynik WHOIS ujawnia dane osobowe,
   które NASK ma obowiązek maskować (RODO), masowy odczyt = poz. 3. Uwaga: samo
   „nie zmaskowane" może być decyzją rejestru — raportować ostrożnie, z analizą
   wpływu, bez masowego zrzutu.

### F. zglos-dezinformacje: ścieżka „podglądu"
Formularz przyjmuje **linki do źródeł dezinformacji** → najpłodniejszy SSRF (serwer
renderuje preview?) + ewentualna generacja PDF/maila z treścią (XSS w PDF / HTML
w mailu = stored, poz. 8 z wpływem). Plus moderacja: jeśli jest panel moderatora,
IDOR na statusach zgłoszeń (P0 kolegi) — pytać o status mojego zgłoszenia zmianą ID.

## 2. Kolejność operacyjna (uzupełnienie tabeli P0–P8)

1. **Dziś–jutro**: user zakłada konto platformy + konta testowe (blokery);
   jsdig na JS 5 aplikacji T1 (pobrane przez przeglądarkę) → mapa endpointów;
   testy A (2 żądania/host), C (ręcznie), `__NEXT_DATA__` zrzuty do analizy offline.
2. **D (WP-with-PoC)** równolegle — najszybsza pierwsza wypłata, zero kont.
3. P0–P2 kolegi na zglos-dezinformacje po założeniu kont (on zaczął).
4. **REJESTR**: wszystko przez wspólny rejestr (przeniesiony do NASK repo) —
   wpisywanie hipotez PRZED testowaniem; first-wins działa też wewnątrz zespołu.

## 3. Uwagi o sprzęcie i narzędziach (zgodnie z preferencjami usera)

- Potwierdzam: **bottleneckiem nie jest compute** (5 req/s na sieć, reszta myślenie).
  Rust+Rayon = offline (JS mining, diff tokenów, entropia, parsowanie __NEXT_DATA__,
  licznik CVSS wektorów) na 5950X; Actions = CI + nocny watch CT/crt.sh (nie dotyka
  celów). Python: gen_report + klejenie JSONL.
- mSzyfr i Gov.pl: OSOBNE programy (03–30.11, 600–20k każdy). mSzyfr odłożony SŁUSZNIE
  (zakres „web" vs aplikacja mobilna do doprecyzowania — chunk 1 regulaminu przeczytać
  przed jakimkolwiek ruchem). Gov.pl = duży portal, duża konkurencja — trzymać w zapasie.

## 4. Czego ja nie zrobię (uczciwie)

Nie mam konta na platformie, nie prowadzę ruchu do celów (sandbox ma sieć tylko do
GitHub/PyPI, a raporty i tak musi wysyłać user z własnego konta). Mój wkład: analiza,
plan, narzędzia offline, quality control raportów (PoC bez nadużywania danych,
minimalne odtworzenie). Wszystkie zgłoszenia = decyzja usera (GO), formularzem.

## 5. Realizm

Najbardziej prawdopodobny scenariusz dochodu tej edycji: **2–5 zgłoszeń klasy
średniej (2 000–4 500 zł) + szansa na jedną wysoką (9k)** przy systematycznej pracy
do 30.11. Krytyczne 20k = loteria wymierzona w świeży kod formularzy (P0–P2) i
stare wtyczki WP (D). Duplikaty = największe ryzyko (platforma świeża) → tempo.
