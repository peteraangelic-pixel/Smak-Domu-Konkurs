# Formularz klucza API — gotowe odpowiedzi

Formularz: https://forms.gle/zz12orkLHTAneLGz6

Tekst poniżej jest spójny z `SUBMISSION.md` — warto, żeby osoba wydająca klucz
i jury przeczytały tę samą historię.

---

## Pole „Project idea" — wersja pełna (~1100 znaków)

```
Smak Domu ("Taste of Home") is a cultural landing planner for people who have
just moved countries. Someone arriving in Poznań from Lviv enters a few things
they love from home — a band, a film, a dish — and gets back a plan for their
first month in the new city: films, places, food, music, podcasts. Every item
explains why it appeared, naming the anchor that pulled it and with what weight.

The agent resolves anchor names to Qloo entity IDs via /search, fans out one
/v2/insights call per domain (all sharing the same anchors, with
feature.explainability=true), composes the plan, then refines it: a "not this"
button feeds filter.exclude.entities and recomputes. Location-aware domains get
filter.location.query set to the destination city.

Qloo is not an add-on here — the affinities, the explainability trail and the
cross-domain taste profile are the entire product. Without it there is nothing
to display. An LLM alone will suggest "try the dumplings" and invent a
restaurant to match; it cannot tell you which arthouse cinema in Poznań
programs films close to Amélie.
```

## Wersja krótka (~430 znaków) — gdy pole ma limit

```
Smak Domu ("Taste of Home") turns "what I loved back home" into a first-month
cultural plan in a new city. The user gives anchors from home — music, film,
food. The agent resolves them via /search, then fans out one /v2/insights call
per domain with feature.explainability=true, and returns films, places, food
and music for their destination city, each showing which anchor drove it. A
"not this" button feeds filter.exclude.entities and recomputes the plan.
```

## Wersja jednozdaniowa

```
A cultural landing planner for new arrivals: it maps the music, films and food
someone loved in their home country onto their new city using Qloo affinities,
and explains every recommendation by naming the anchor that drove it.
```

---

## Dlaczego tak to jest napisane

Osoba wydająca klucz sprawdza jedno: **czy ten projekt realnie zużyje API**.
Dlatego tekst:

- wymienia konkretne endpointy i parametry (`/search`, `/v2/insights`,
  `feature.explainability`, `filter.location.query`, `filter.exclude.entities`)
  — to sygnał, że dokumentacja została przeczytana, nie przepisany pomysł,
- mówi wprost, co się stanie bez Qloo („there is nothing to display"),
- pokazuje pętlę agentową, a nie jednorazowe zapytanie — to odróżnia projekt
  agentowy od zwykłego wrapper'a.

## Uwaga o trybie demo

Aplikacja działa teraz na deterministycznych fixture'ach i pokazuje o tym
baner. **Nie pisz w formularzu, że demo już działa na Qloo** — to nieprawda,
a klucze wydaje ta sama firma, która będzie oceniać zgłoszenie.
