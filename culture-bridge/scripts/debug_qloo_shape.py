"""Diagnostyka kształtu odpowiedzi Qloo — uruchamiana w GitHub Actions.

Wypisuje STRUKTURĘ odpowiedzi (klucze, typy, status HTTP), nie treść zapytań
ani klucz. Służy do sprawdzenia, czy parser (qloo_client.py) rozumie prawdziwe
odpowiedzi hackathonowego API: wyjaśnialność, rozwiązywanie kotwic, pozycje.
"""

from __future__ import annotations

import json
import os
import sys

import httpx

BASE = os.environ.get("QLOO_BASE_URL", "https://hackathon.api.qloo.com").rstrip("/")
KEY = os.environ.get("QLOO_API_KEY", "").strip()
HEADERS = {"X-Api-Key": KEY, "accept": "application/json"}


def shape(obj, depth=0, max_depth=4):
    """Zwraca czytelny opis struktury (klucze i typy), bez wartości."""
    pad = "  " * depth
    if depth > max_depth:
        return f"{pad}...\n"
    if isinstance(obj, dict):
        out = ""
        for k, v in list(obj.items())[:25]:
            if isinstance(v, (dict, list)):
                out += f"{pad}{k}: {type(v).__name__}({len(v)})\n" + shape(v, depth + 1, max_depth)
            else:
                sample = str(v)[:60].replace("\n", " ")
                out += f"{pad}{k}: {type(v).__name__} = {sample!r}\n"
        return out
    if isinstance(obj, list):
        if not obj:
            return f"{pad}[] (pusta lista)\n"
        return shape(obj[0], depth + 1, max_depth)
    return f"{pad}{type(obj).__name__}\n"


def call(client: httpx.Client, label: str, path: str, params: dict):
    print(f"\n===== {label}  GET {path} params={sorted(params)}")
    r = client.get(path, params=params)
    print(f"HTTP {r.status_code}")
    try:
        data = r.json()
    except ValueError:
        print("nie-JSON:", r.text[:300])
        return None
    if r.status_code != 200:
        print("body:", json.dumps(data, ensure_ascii=False)[:400])
        return None
    print(shape(data))
    return data


def first_entity_id(data, want_name: str | None = None):
    results = (data or {}).get("results")
    if isinstance(results, dict):
        results = results.get("results") or results.get("entities") or []
    if not isinstance(results, list):
        return None, None
    for item in results:
        if want_name is None or want_name.lower() in str(item.get("name", "")).lower():
            return item.get("entity_id"), item.get("name")
    return None, None


def main() -> int:
    if not KEY:
        print("Brak QLOO_API_KEY.")
        return 1
    with httpx.Client(base_url=BASE, headers=HEADERS, timeout=30) as c:
        # 1. Rozwiązywanie kotwic: bez filtra typu i z filtrem artist.
        s1 = call(c, "search Okean Elzy (bez typu)", "/search", {"query": "Okean Elzy", "take": 3})
        s2 = call(
            c,
            "search Okean Elzy (artist)",
            "/search",
            {"query": "Okean Elzy", "types": "urn:entity:artist", "take": 3},
        )
        s3 = call(c, "search Amelie (movie)", "/search", {"query": "Amelie", "types": "urn:entity:movie", "take": 3})

        amelie_id, amelie_name = first_entity_id(s3)
        print(f"\nAmélie id={'OK' if amelie_id else 'BRAK'} name={amelie_name!r}")

        # 2. Insights z wyjaśnialnością — kluczowe dla „dlaczego”.
        if amelie_id:
            ins = call(
                c,
                "insights movie, interest=Amelie, explainability",
                "/v2/insights",
                {
                    "filter.type": "urn:entity:movie",
                    "signal.interests.entities": amelie_id,
                    "feature.explainability": "true",
                    "take": 3,
                    "page": 1,
                },
            )
            if ins:
                results = ins.get("results")
                items = results.get("results") if isinstance(results, dict) else results
                if isinstance(items, list) and items:
                    first = items[0]
                    print("\n--- pierwsza pozycja: klucze top-level:", sorted(first.keys()))
                    print("--- klucz 'query' (pełna struktura):")
                    print(shape(first.get("query"), depth=1, max_depth=6) if first.get("query") is not None else "BRAK pola query")
                    print("--- raw query (obcięte do 900 znaków, bez wartości wrażliwych):")
                    print(json.dumps(first.get("query"), ensure_ascii=False)[:900])
                else:
                    print("\nBrak pozycji w wyniku insights.")

        # 3. Insights bez wyjaśnialności — porównanie, czy pole query pojawia się tylko z flagą.
        if amelie_id:
            call(
                c,
                "insights movie, interest=Amelie, BEZ explainability",
                "/v2/insights",
                {"filter.type": "urn:entity:movie", "signal.interests.entities": amelie_id, "take": 1, "page": 1},
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
