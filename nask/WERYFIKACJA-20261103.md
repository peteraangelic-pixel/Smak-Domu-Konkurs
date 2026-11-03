# WERYFIKACJA — 03.11.2026 (sesja Smak)

Metoda: fakty programu sprawdzone u źródeł (strona hack.cert.pl pobrana i przeczytana dziś,
artykuł android.com.pl, regulaminy wyciąg c87 + PDF TXT codex), twierdzenia kolegów ocenione
na ich kodzie/artefaktach, nie na deklaracjach. Zgodnie z regułą kampanii ARC: cudze liczby
weryfikować samodzielnie.

## 1. Fakty programu — ZWERYFIKOWANE PRZEZE MNIE u źródła

| fakt | wartość | źródło |
|---|---|---|
| platforma | hack.cert.pl = pierwszy państwowy bug bounty (CERT Polska/NASK), start **3.11.2026** | strona + artykuł |
| edycja 11/2026 (NASK) | **3–30.11.2026**, pula 100 000 zł (platforma łącznie ~1 mln wg artykułu; 410k suma pul 5 programów wg codex) | regulamin (c87 wyciąg) + codex porównanie |
| stawki NASK Tier 1 | **600 / 4 000 / 9 000 / 20 000 PLN** (CVSS 4.0: 0.1–3.9 / 4.0–6.9 / 7.0–8.9 / 9.0–10.0) | zgodne: c87, codex, strona |
| stawki Tier 2 | 300 / 2 000 / 4 500 / 10 000 PLN | j.w. |
| Tier 1 hosts (5) | `nask.pl`, `dyzurnet.pl`, `dns.pl`, `oad.nask.pl`, `zglos-dezinformacje.nask.pl` | zgodne (3 źródła) |
| Tier 2 hosts (7) | `bezpiecznymiesiac.pl`, `secure.edu.pl`, `bezpiecznewybory.pl`, `116sos.pl`, `pllum.org.pl`, `science.nask.pl`, `dataannotation.pllum.org.pl` | j.w. |
| limity | **max 5 req/s** na automatyczne narzędzia; tylko brak auth albo WŁASNE konta; DoS/obciążenie ZABRONIONE | regulamin §6, §8 |
| kwalifikacja | PoC + odtworzenie OBOWIĄZKOWE; sam skaner = odrzucone; duplikat → wygrywa wcześniejsza data+godzina; ta sama przyczyna w wielu serwisach = 1 nagroda | regulamin §7–8 |
| uczestnik | 18+, polska rezydencja podatkowa, rejestracja na platformie | regulamin §4 |
| wypłata | rozstrzyganie sukcesywne; wyniki do 30 dni po edycji; wypłata do 60 dni; NASK odprowadza podatek zryczałtowany (kwota netto dla zwycięzcy); potwierdzenie wygranej w 7 dni | regulamin §7 + codex |

**Wniosek prawny (krytyczny):** zakres = DOKŁADNIE 12 hostów. Subdomeny (`*.nask.pl` poza
listą), zaplecza, API dostawców — POZA programem; testowanie ich to naruszenie prawa, nie
„brak nagrody". Limit 5 req/s twardy. To wyklucza klasyczne skanowanie masowe — gra jest o
myśleniu i jakości raportu.

## 2. Praca kolegów — co sprawdziłem, co przyjmuję

| element | autor | moja weryfikacja | werdykt |
|---|---|---|---|
| pakiet `nask/` (regulamin, strategia, rekonesans, rejestr, naskrecon) | c87 (Pokemon d820f0e + Drive 13 plików) | strategia i wyciąg regulaminu spójne z moim odczytem źródeł; mapy celów nie mogę potwierdzić bez własnego ruchu sieciowego (nie powtarzałem) | PRZYJĘTE jako baza |
| `naskrecon` (Rust+Rayon: limiter globalny, guard dokładnych hostów, odcinanie catch-all) | paczka Drive / c87 czytał kod | c87 potwierdził limiter+guard+testy (16) przez czytanie kodu; nikt nie odpalił pełnego biegu; **ja nie mam cargo w sandboxie — nie uruchamiałem** | przyjmuję z zastrzeżeniem „nieuruchomione" |
| porównanie 5 programów + PDF-y regulaminów | codex (`codex/multi-program-lab-20261103`) | liczby spójne z moją weryfikacją; rekomendacja „NASK pierwszy, CERT drugi" sensowna (różnorodność aplikacji vs jeden portal) | PRZYJĘTE |
| „następny etap": `zglos-dezinformacje.nask.pl` jako pierwsza funkcja do pogłębienia; HIVE odłożone (konto zaproszeniowe) | codex | zgodne z moją oceną powierzchni ataku (formularz+upload+PII = Tier 1) | PRZYJĘTE |
| skaner takeover (main, ed96a2f) | Arena a29ca234 | codex: „nie jest gotowy do użycia; commit nie naprawił błędów narzędzi i CI" | NIE używać bez przebudowy |
| repo NASK main | — | tylko README (potwierdzone) | praca na gałęziach |

## 3. Korekty / luki, które widzę (moja wartość dodana)

1. **Brak wspólnego rejestru pracy między sesjami.** Reguła „kto pierwszy, ten lepszy"
   obowiązuje też NAS: jeśli ja i codex znajdziemy ten sam bug, zgłosimy duplikat.
   Potrzebny JEDEN rejestr hipotez/testów (bazą jest `REJESTR-ZGLOSZEN.md` c87 — ale on
   leży w Pokemon repo; przenosimy do NASK repo jako główne źródło prawdy).
2. **Nikt nie uruchomił jeszcze nic na żywo** (0 potwierdzonych podatności; codex planuje
   sesję 45+45+30 min na formularzu). To normalne na dzień 1.
3. **Brak warstwy „lokalna analiza JS/assetów"** — a to jest bez limitów (pliki i tak
   przegląda przeglądarka), CPU-bound i idealne pod Rust/Rayon + 5950X. Tego nikt nie
   zaplanował konkretnie.
4. **Konta testowe**: bez zalogowanego konta nie zobaczymy klas płatnych (IDOR/BAC,
   role, sesje). User musi założyć konto na hack.cert.pl + konta testowe w aplikacjach
   (zglos-dezinformacje, dyzurnet, dns.pl/EPP?, science.nask.pl, 116sos, bezpiecznymiesiac).
5. mSzyfr: odłożony przez codex (kontrowersja zakresu web vs aplikacja mobilna) — SŁUSZNIE;
   wraca dopiero po jasnym wskazaniu zakresu w regulaminie programu.
