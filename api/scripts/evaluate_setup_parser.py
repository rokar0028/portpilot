"""Run an opt-in live parser evaluation; provider calls incur provider privacy/cost terms."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("external_displays", "resolution", "refresh_rate_hz", "laptop_charging")


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from app.setup_parser import parse_setup

    cases = json.loads((ROOT / "evaluations" / "phase8_setup_prompts.json").read_text())
    matched = dict.fromkeys(FIELDS, 0)
    totals = dict.fromkeys(FIELDS, 0)
    clarification_correct = 0
    clarification_total = 0
    failures: list[str] = []

    for case in cases:
        result = parse_setup(case["prompt"])
        actual = result.setup.model_dump()
        for field in FIELDS:
            if field in case["expected"]:
                totals[field] += 1
                matched[field] += actual[field] == case["expected"][field]
        if "expect_clarification" in case:
            clarification_total += 1
            clarification_correct += result.needs_clarification == case["expect_clarification"]
        if "expect_unsupported" in case and bool(result.unsupported_requests) != case["expect_unsupported"]:
            failures.append(f"{case['id']}: unsupported request was not surfaced as expected")
        if any(actual[field] != expected for field, expected in case["expected"].items()):
            failures.append(f"{case['id']}: field mismatch")

    print("Phase 8 parser evaluation (live provider; parsing only)")
    print(f"Cases: {len(cases)}")
    for field in FIELDS:
        print(f"{field}: {matched[field]}/{totals[field]} exact ({matched[field] / totals[field]:.0%})")
    if clarification_total:
        print(f"clarification: {clarification_correct}/{clarification_total} expected cases")
    print(f"Failures: {len(failures)}")
    for failure in failures:
        print(f"- {failure}")


if __name__ == "__main__":
    main()
