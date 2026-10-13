"""Test na żywym API Qloo — uruchamiany w GitHub Actions (sekret QLOO_API_KEY).

Nie drukuje klucza. Kończy się kodem 1, jeśli plan nie pochodzi z Qloo
albo jest pusty — wtedy wiadomo, że checklista „sprawdzone na prawdziwych
kotwicach” NIE jest zaliczona.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings  # noqa: E402
from app.models import Anchor, PlanRequest  # noqa: E402
from app.narrator import build_narrator  # noqa: E402
from app.planner import Planner  # noqa: E402
from app.provider import build_provider  # noqa: E402

ANCHORS = [
    Anchor(name="Okean Elzy", kind="artist"),
    Anchor(name="Amélie", kind="movie"),
    Anchor(name="barszcz", kind="dish"),
]


def main() -> int:
    settings = load_settings()
    if not settings.qloo_enabled:
        print("FAIL: brak QLOO_API_KEY w środowisku — test nie ma sensu bez klucza.")
        return 1

    provider, source = build_provider(settings)
    narrator, _ = build_narrator(settings)
    planner = Planner(provider, source, narrator=narrator)

    request = PlanRequest(origin="Lwów", destination="Poznań", anchors=ANCHORS)
    plan = planner.build_plan(request)

    print(f"data_source={plan.data_source} qloo_calls={plan.qloo_calls}")
    for w in plan.warnings:
        print(f"warning: {w}")

    total = 0
    for section in plan.sections:
        print(f"\n## {section.label} ({len(section.items)} pozycji)")
        total += len(section.items)
        for item in section.items[:5]:
            print(f"- {item.name} [affinity {item.affinity:.2f}] — {item.why}")
            print(f"  source={item.source}")

    # Zapis do pliku, żeby można go dołączyć jako artefakt w Actions.
    out = Path("live_check_result.json")
    out.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    failures = []
    if any(i.source != "qloo" for s in plan.sections for i in s.items):
        failures.append("część pozycji pochodzi z fixture'ów (source != qloo)")
    if plan.data_source != "qloo":
        failures.append(f"data_source={plan.data_source}, oczekiwano qloo")
    if plan.qloo_calls == 0:
        failures.append("zero zapytań do Qloo")
    if total == 0:
        failures.append("plan bez żadnej pozycji")
    if len([s for s in plan.sections if s.items]) < 2:
        failures.append("mniej niż 2 sekcje z pozycjami")

    if failures:
        print("\nFAIL:\n- " + "\n- ".join(failures))
        return 1
    print(f"\nOK: {total} pozycji z Qloo w {len(plan.sections)} sekcjach.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
