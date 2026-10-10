# Tekst do wklejenia w nowej sesji Arena

Skopiuj wszystko poniżej linii i wklej jako pierwszą wiadomość.

---

Kontynuuję zgłoszenie do **Qloo Agentic Hackathon** (termin **30.10.2026 23:45 EDT**,
zostało ~20 dni). Komunikujemy się po polsku.

## Repo

`peteraangelic-pixel/KonkursyMat`, zgłoszenie w katalogu `culture-bridge/`.
Projekt: **Smak Domu / Culture Bridge** — agentowy plan kulturowego lądowania dla
osób, które właśnie zmieniły kraj. Użytkownik podaje kotwice smakowe z kraju
pochodzenia (muzyka, film, jedzenie), a Qloo Insights API zamienia to w plan
pierwszego miesiąca w nowym mieście, z wyjaśnieniem przy każdej pozycji.

Stack: FastAPI + vanilla JS, bez etapu budowania frontendu. **89 testów.**

## Stan na teraz — co już jest zrobione

Na `main` (po merge PR #1, commit `78dfbea`):

- kompletna aplikacja w `culture-bridge/` (2757 linii Pythona)
- licencja **MIT wykryta przez GitHuba** — wymóg konkursu spełniony
- CI: testy na Pythonie 3.11 i 3.12 + smoke test serwera (`.github/workflows/ci.yml`)
- `render.yaml` **w korzeniu repo** z `rootDir: culture-bridge`
- `culture-bridge/SUBMISSION.md` — gotowy tekst zgłoszenia na Devpost
- `culture-bridge/API_KEY_FORM.md` — gotowe odpowiedzi do formularza klucza API

## Pierwsza rzecz do zrobienia

Commit `74b08d9` z plikiem `culture-bridge/API_KEY_FORM.md` istniał **tylko lokalnie**
w poprzedniej sesji i nigdy nie trafił na GitHub. Sprawdź, czy ten plik jest na
dysku, i jeśli tak — wypchnij go. Jeśli go nie ma, treść jest odtwarzalna z
`SUBMISSION.md` (to te same fakty, tylko skrócone do pola formularza).

## Co zostało (checklista w `culture-bridge/README.md`)

1. **`QLOO_API_KEY`** — formularz https://forms.gle/zz12orkLHTAneLGz6, wydawany
   ręcznie, kilka dni roboczych. Bez niego aplikacja działa w trybie demo na
   fixture'ach i **nie może być zgłoszona** jako demo (wymóg: demo hostowane
   i w pełni opublikowane zewnętrznie).
2. **Deploy na Render** — konfiguracja gotowa i przetestowana na czystym klonie
   (instalacja, start na `$PORT`, health check → wszystko 200).
3. **Opis w sekcji About na GitHubie** — pole Description jest puste.
   Poprzednia sesja dostała `HTTP 403` przy `gh repo edit`, więc to trzeba
   zrobić kliknięciem w przeglądarce.

## Pułapki, które już kosztowały czas — nie powtarzaj

Wszystkie cztery bugi poniżej **przechodziły testy** i ujawniłyby się dopiero
z prawdziwym kluczem. Są naprawione, ale warto wiedzieć, gdzie były:

- **Kształt odpowiedzi Qloo.** Encje mają `entity_id`, nie `id`. `tags` to lista
  słowników `{id, name, type}`, nie napisów. Obrazek siedzi w
  `properties.image.url`. Afinacja jest w `query.affinity`, a `popularity` to
  co innego. Parser jest napisany pod udokumentowany przykład odpowiedzi,
  nie pod listę parametrów.
- **Rozmiar wyniku to `take` (1–50), nie `size`.** Zmyślony parametr jest po
  cichu ignorowany — API zwraca 200 z pustą listą zamiast błędu. Jest test
  pilnujący dokładnego zbioru wysyłanych parametrów.
- **`/search` zwraca 404 „No results"** — to normalny wynik, nie awaria.
- **401/403 i awaria sieci muszą przerywać plan jako 502**, nie degradować się
  do pustej sekcji. Zły klucz dotyczy każdego zapytania, a połknięty błąd
  wyglądał identycznie jak „brak danych dla tego miasta". Klasa
  `QlooFatalError` (z podklasami `QlooAuthError`, `QlooConnectionError`) jest
  przepuszczana wyżej przez planer; zwykły `QlooError` nadal degraduje się per
  domena.
- **Klucz hackathonowy działa wyłącznie z `https://hackathon.api.qloo.com`**
  i idzie w nagłówku `X-Api-Key`. `api.qloo.com` zwróci 401.

## Środowisko

Venv jest w **korzeniu repo** (`/home/user/KonkursyMat/.venv`), nie w
`culture-bridge/`. Przed testami: `. .venv/bin/activate`, potem
`cd culture-bridge && python -m pytest tests/ -q`.

## Czego NIE robić

Nie pisz w formularzu klucza ani w zgłoszeniu, że demo już działa na Qloo.
Aplikacja jest na fixture'ach i pokazuje o tym baner — a klucze wydaje ta sama
firma, która ocenia zgłoszenie.
