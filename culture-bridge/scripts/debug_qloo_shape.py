"""Diagnostyka odpowiedzi Qloo — uruchamiana w GitHub Actions.

Wypisuje surowe fragmenty odpowiedzi potrzebne do poprawnego parsowania
(wyjaśnialność, rozwiązywanie artystów). NIE wypisuje klucza API ani nagłówków.
"""

from __future__ import annotations

import json
import os
import sys
import time

import httpx

BASE = os.environ.get("QLOO_BASE_URL", "https://hackathon.api.qloo.com").rstrip("/")
KEY = os.environ.get("QLOO_API_KEY", "").strip()
HEADERS = {"X-Api-Key": KEY, "accept": "application/json"}
MAX = 2500


def items_of(payload):
    results = (payload or {}).get("results")
    if isinstance(results, dict):
        return results.get("entities") or results.get("results") or []
    return results if isinstance(results, list) else []


def get(client, label, path, params):
    print(f"\n===== {label}  HTTP ", end="")
    time.sleep(2)  # limit zapytań: nie strzelamy seriami
    r = client.get(path, params=params)
    for _ in range(3):
        if r.status_code != 429:
            break
        time.sleep(5)
        r = client.get(path, params=params)
    print(r.status_code)
    try:
        data = r.json()
    except ValueError:
        print("nie-JSON")
        return None
    if r.status_code != 200:
        print(json.dumps(data, ensure_ascii=False)[:300])
        return None
    return data


def main() -> int:
    if not KEY:
        print("Brak QLOO_API_KEY.")
        return 1
    with httpx.Client(base_url=BASE, headers=HEADERS, timeout=30) as c:
        # 1. Artyści: które nazwy są w katalogu jako urn:entity:artist?
        for name in ["Okean Elzy", "Okean Elza", "Pixies", "Radiohead", "Skalpel", "Czesław Niemen"]:
            d = get(c, f"search artist '{name}'", "/search", {"query": name, "types": "urn:entity:artist", "take": 3})
            if d is not None:
                for it in d.get("results", [])[:3]:
                    print(f"   -> {it.get('name')!r} id={it.get('entity_id')} subtype={it.get('subtype') or it.get('types')}")

        # 2. Amélie jako kotwica filmu.
        d = get(c, "search movie 'Amelie'", "/search", {"query": "Amelie", "types": "urn:entity:movie", "take": 1})
        amelie = (d or {}).get("results", [{}])[0].get("entity_id") if d and d.get("results") else None
        print("Amélie id:", amelie)

        if amelie:
            # 3. Insights z wyjaśnialnością — surowe `query` pierwszej pozycji i top-level `query`.
            ins = get(
                c,
                "insights movie, interest=Amelie, explainability",
                "/v2/insights",
                {"filter.type": "urn:entity:movie", "signal.interests.entities": amelie,
                 "feature.explainability": "true", "take": 2, "page": 1},
            )
            if ins:
                print("\n--- top-level keys:", sorted(ins.keys()))
                print("--- top-level 'query' (surowo):")
                print(json.dumps(ins.get("query"), ensure_ascii=False, indent=1)[:MAX])
                its = items_of(ins)
                print(f"\n--- liczba pozycji: {len(its)}")
                for it in its[:2]:
                    print(f"--- pozycja {it.get('name')!r}: klucze query = {sorted((it.get('query') or {}).keys())}")
                    print("--- item['query'] (surowo):")
                    print(json.dumps(it.get("query"), ensure_ascii=False, indent=1)[:MAX])
    return 0


if __name__ == "__main__":
    sys.exit(main())
