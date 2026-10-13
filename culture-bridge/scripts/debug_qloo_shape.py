"""Diagnostyka jedzenia i miejsc w Qloo — uruchamiana w GitHub Actions.

Sprawdza, czy kotwica kulinarna (np. barszcz) działa jako sygnał dla miejsc
w Poznaniu. NIE wypisuje klucza API.
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


def get(client: httpx.Client, label: str, path: str, params: dict):
    print(f"\n===== {label}")
    for attempt in range(4):
        time.sleep(2)
        r = client.get(path, params=params)
        if r.status_code != 429:
            break
        print(f"  429, czekam ({attempt + 1})")
        time.sleep(5)
    print(f"  HTTP {r.status_code}")
    try:
        data = r.json()
    except ValueError:
        print("  nie-JSON:", r.text[:200])
        return None
    if r.status_code != 200:
        print("  body:", json.dumps(data, ensure_ascii=False)[:300])
        return None
    return data


def entities(payload):
    results = (payload or {}).get("results")
    if isinstance(results, dict):
        return results.get("entities") or results.get("results") or []
    return results if isinstance(results, list) else []


def show(items, n=6):
    for it in items[:n]:
        drivers = (it.get("query") or {}).get("explainability", {}).get("signal.interests.entities", [])
        print(
            f"  - {it.get('name')!r} subtype={it.get('subtype')} "
            f"aff={(it.get('query') or {}).get('affinity')} drivers={len(drivers)}"
        )


def main() -> int:
    if not KEY:
        print("Brak QLOO_API_KEY.")
        return 1
    with httpx.Client(base_url=BASE, headers=HEADERS, timeout=30) as c:
        # 1. Czy barszcz / pierogi są encjami w katalogu?
        barszcz_id = None
        for q in ["barszcz", "borscht", "pierogi"]:
            d = get(c, f"search '{q}' (bez typu)", "/search", {"query": q, "take": 3})
            for it in entities(d)[:3]:
                print(f"  -> {it.get('name')!r} id={it.get('entity_id')} subtype={it.get('subtype')} types={it.get('types')}")
                if q == "barszcz" and barszcz_id is None:
                    barszcz_id = it.get("entity_id")

        # 2. Tagi (endpoint z przewodnika) — szukamy tagów kuchni polskiej.
        for q in ["polish", "polska", "soup"]:
            d = get(c, f"tags '{q}' (/v2/tags)", "/v2/tags", {"query": q})
            if d is not None:
                for t in (d.get("results") or [])[:5]:
                    print(f"  -> tag {t.get('name')!r} id={t.get('id') or t.get('tag_id')} type={t.get('type')}")

        # 3. Miejsca w Poznaniu z kotwicą kulinarną — czy barszcz w ogóle wpływa?
        if barszcz_id:
            d = get(
                c,
                "place Poznań, interest=barszcz, explainability",
                "/v2/insights",
                {
                    "filter.type": "urn:entity:place",
                    "signal.interests.entities": barszcz_id,
                    "filter.location.query": "Poznań",
                    "feature.explainability": "true",
                    "take": 6,
                    "page": 1,
                },
            )
            show(entities(d))

        # 4. Miejsca w Poznaniu bez kotwicy (punkt odniesienia).
        d = get(
            c,
            "place Poznań, BEZ kotwicy",
            "/v2/insights",
            {"filter.type": "urn:entity:place", "filter.location.query": "Poznań", "take": 6, "page": 1},
        )
        show(entities(d))

        # 5. Restauracje: typ brand i tag kuchni (jeśli /v2/tags coś zwrócił, użyjemy go w kolejnym kroku).
        d = get(
            c,
            "brand, interest=barszcz",
            "/v2/insights",
            {"filter.type": "urn:entity:brand", "signal.interests.entities": barszcz_id or "", "take": 6, "page": 1}
            if barszcz_id
            else {"filter.type": "urn:entity:brand", "take": 1, "page": 1},
        )
        show(entities(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
