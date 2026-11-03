"""Run an opt-in setup parser evaluation against a configured provider or mock harness.

Live provider calls incur provider privacy, terms, and cost. Evaluation measures
natural-language requirement extraction fidelity only, NOT hardware compatibility.
Compatibility rules remain 100% deterministic and separately evaluated.
"""

import argparse
import json
import os
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPTS = ROOT / "evaluations" / "v2_setup_prompts.json"
LEGACY_PROMPTS = ROOT / "evaluations" / "phase8_setup_prompts.json"
FIELDS = ("external_displays", "resolution", "refresh_rate_hz", "laptop_charging")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PortPilot Setup Parser Evaluation Benchmark Runner.")
    parser.add_argument(
        "--prompts-file",
        type=Path,
        default=DEFAULT_PROMPTS if DEFAULT_PROMPTS.exists() else LEGACY_PROMPTS,
        help="Path to the JSON prompts benchmark file.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to write a machine-readable JSON evaluation report.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=None,
        help="Optional path to write a formatted Markdown evaluation report.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run against a deterministic mock responder (for offline regression testing/CI).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the prompt benchmark schema without executing queries.",
    )
    return parser.parse_args()


def load_cases(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Prompts file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError(f"Prompts file must contain a non-empty list of test cases: {path}")
    return data


def run_evaluation(cases: list[dict], mock: bool = False) -> dict:
    sys.path.insert(0, str(ROOT))
    from app.schemas import SetupParseResponse, SetupRequest
    from app.setup_parser import parse_setup

    provider_host = "mock-internal" if mock else "unconfigured"
    model_name = "mock-model" if mock else os.getenv("SETUP_PARSER_MODEL", "unknown")
    if not mock:
        raw_base = os.getenv("SETUP_PARSER_BASE_URL", "").strip()
        if raw_base:
            parsed_url = urlparse(raw_base)
            provider_host = parsed_url.netloc or parsed_url.path

    latencies_ms: list[float] = []
    matched = dict.fromkeys(FIELDS, 0)
    totals = dict.fromkeys(FIELDS, 0)
    exact_all_matches = 0

    category_stats: dict[str, dict[str, int]] = {}

    clarification_expected_total = 0
    clarification_actual_total = 0
    clarification_true_positive = 0
    clarification_correct = 0

    unsupported_expected_total = 0
    unsupported_detected = 0

    failures: list[dict] = []
    case_results: list[dict] = []

    for case in cases:
        case_id = case.get("id", "unknown")
        category = case.get("category", "uncategorized")
        if category not in category_stats:
            category_stats[category] = {"total": 0, "exact": 0}
        category_stats[category]["total"] += 1

        prompt = case["prompt"]
        expected = case.get("expected", {})
        expect_clarification = case.get("expect_clarification", False)
        expect_unsupported = case.get("expect_unsupported", False)

        started = time.perf_counter()
        if mock:
            # Deterministic mock simulation
            time.sleep(0.001)
            raw_displays = expected.get("external_displays")
            mock_displays = raw_displays if (raw_displays is None or 0 <= raw_displays <= 4) else None
            result = SetupParseResponse(
                setup=SetupRequest(
                    external_displays=mock_displays,
                    resolution=expected.get("resolution"),
                    refresh_rate_hz=expected.get("refresh_rate_hz"),
                    laptop_charging=expected.get("laptop_charging"),
                ),
                needs_clarification=expect_clarification,
                clarification_questions=["Please clarify requirements."] if expect_clarification else [],
                unsupported_requests=["Unsupported peripheral requested."] if expect_unsupported else [],
            )
        else:
            result = parse_setup(prompt)

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        latencies_ms.append(elapsed_ms)

        actual_setup = result.setup.model_dump()
        field_matches: dict[str, bool] = {}
        all_fields_matched = True

        for field in FIELDS:
            if field in expected:
                totals[field] += 1
                is_match = actual_setup[field] == expected[field]
                field_matches[field] = is_match
                if is_match:
                    matched[field] += 1
                else:
                    all_fields_matched = False

        if all_fields_matched:
            exact_all_matches += 1
            category_stats[category]["exact"] += 1

        # Clarification tracking
        if expect_clarification:
            clarification_expected_total += 1
        if result.needs_clarification:
            clarification_actual_total += 1
        if expect_clarification and result.needs_clarification:
            clarification_true_positive += 1
        if result.needs_clarification == expect_clarification:
            clarification_correct += 1

        # Unsupported requests tracking
        has_unsupported = bool(result.unsupported_requests)
        if expect_unsupported:
            unsupported_expected_total += 1
            if has_unsupported:
                unsupported_detected += 1

        case_failed = not all_fields_matched or (result.needs_clarification != expect_clarification)
        if case_failed:
            failures.append(
                {
                    "id": case_id,
                    "category": category,
                    "prompt": prompt,
                    "expected": expected,
                    "actual": actual_setup,
                    "expected_clarification": expect_clarification,
                    "actual_clarification": result.needs_clarification,
                    "expected_unsupported": expect_unsupported,
                    "actual_unsupported": result.unsupported_requests,
                }
            )

        case_results.append(
            {
                "id": case_id,
                "category": category,
                "latency_ms": elapsed_ms,
                "all_fields_matched": all_fields_matched,
                "actual_setup": actual_setup,
                "needs_clarification": result.needs_clarification,
                "unsupported_requests": result.unsupported_requests,
            }
        )

    # Compute latency percentiles
    latencies_sorted = sorted(latencies_ms)
    p50 = statistics.median(latencies_sorted) if latencies_sorted else 0.0
    p95 = (
        latencies_sorted[int(len(latencies_sorted) * 0.95)]
        if len(latencies_sorted) >= 20
        else max(latencies_sorted)
        if latencies_sorted
        else 0.0
    )

    clarification_recall = (
        (clarification_true_positive / clarification_expected_total)
        if clarification_expected_total > 0
        else 1.0
    )
    unsupported_recall = (
        (unsupported_detected / unsupported_expected_total) if unsupported_expected_total > 0 else 1.0
    )

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "mock" if mock else "live",
        "provider_host": provider_host,
        "model": model_name,
        "total_cases": len(cases),
        "overall_exact_match_rate": round(exact_all_matches / len(cases), 4) if cases else 0.0,
        "fields": {
            field: {
                "matched": matched[field],
                "total": totals[field],
                "accuracy": round(matched[field] / totals[field], 4) if totals[field] > 0 else 0.0,
            }
            for field in FIELDS
        },
        "categories": {
            cat: {
                "exact": stats["exact"],
                "total": stats["total"],
                "accuracy": round(stats["exact"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
            }
            for cat, stats in category_stats.items()
        },
        "clarification": {
            "expected_cases": clarification_expected_total,
            "actual_triggered": clarification_actual_total,
            "correct_decisions": clarification_correct,
            "recall": round(clarification_recall, 4),
        },
        "unsupported": {
            "expected_cases": unsupported_expected_total,
            "detected": unsupported_detected,
            "recall": round(unsupported_recall, 4),
        },
        "latency_ms": {
            "min": min(latencies_ms) if latencies_ms else 0.0,
            "median": round(p50, 2),
            "p95": round(p95, 2),
            "max": max(latencies_ms) if latencies_ms else 0.0,
        },
        "failure_count": len(failures),
        "failures": failures,
        "case_results": case_results,
    }
    return report


def render_markdown(report: dict) -> str:
    lines = [
        "# PortPilot Setup Parser Evaluation Report",
        "",
        f"- **Timestamp:** `{report['timestamp']}`",
        f"- **Execution Mode:** `{report['mode'].upper()}`",
        f"- **Provider Host:** `{report['provider_host']}`",
        f"- **Model Identifier:** `{report['model']}`",
        f"- **Total Prompts Evaluated:** `{report['total_cases']}`",
        f"- **Overall Exact Setup Match Rate:** `{report['overall_exact_match_rate']:.1%}`",
        f"- **Clarification Recall:** `{report['clarification']['recall']:.1%}`",
        f"- **Unsupported Requests Recall:** `{report['unsupported']['recall']:.1%}`",
        "",
        "### Latency Statistics (Server-to-Provider Roundtrip)",
        "",
        f"- **Min:** {report['latency_ms']['min']:.1f} ms",
        f"- **Median (p50):** {report['latency_ms']['median']:.1f} ms",
        f"- **p95:** {report['latency_ms']['p95']:.1f} ms",
        f"- **Max:** {report['latency_ms']['max']:.1f} ms",
        "",
        "### Per-Field Extraction Accuracy",
        "",
        "| Field | Correct | Evaluated | Accuracy |",
        "|---|:---:|:---:|:---:|",
    ]
    for field, data in report["fields"].items():
        lines.append(f"| `{field}` | {data['matched']} | {data['total']} | {data['accuracy']:.1%} |")

    lines.extend(
        [
            "",
            "### Category Breakdown",
            "",
            "| Category | Exact Matches | Total | Match Rate |",
            "|---|:---:|:---:|:---:|",
        ]
    )
    for cat, data in report["categories"].items():
        lines.append(f"| `{cat}` | {data['exact']} | {data['total']} | {data['accuracy']:.1%} |")

    lines.extend(
        [
            "",
            f"### Failure Analysis ({report['failure_count']} cases)",
            "",
        ]
    )
    if not report["failures"]:
        lines.append("No extraction failures observed in this run.")
    else:
        for failure in report["failures"]:
            lines.extend(
                [
                    f"#### Case `{failure['id']}` (`{failure['category']}`)",
                    f'- **Prompt:** "{failure["prompt"]}"',
                    f"- **Expected Setup:** `{json.dumps(failure['expected'])}`",
                    f"- **Actual Setup:** `{json.dumps(failure['actual'])}`",
                    f"- **Clarification:** expected `{failure['expected_clarification']}`, "
                    f"got `{failure['actual_clarification']}`",
                    f"- **Unsupported:** expected `{failure['expected_unsupported']}`, "
                    f"got `{failure['actual_unsupported']}`",
                    "",
                ]
            )

    lines.extend(
        [
            "",
            "> [!NOTE]",
            "> This benchmark measures AI natural-language setup interpretation accuracy only.",
            "> Hardware compatibility verdicts are 100% deterministic and evaluated separately",
            "> by the PortPilot rules engine.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    cases = load_cases(args.prompts_file)

    if args.dry_run:
        print(f"Validated benchmark format: {args.prompts_file} ({len(cases)} cases)")
        categories = sorted({c.get("category", "uncategorized") for c in cases})
        print(f"Categories present ({len(categories)}): {', '.join(categories)}")
        return

    report = run_evaluation(cases, mock=args.mock)

    # Print summary to stdout
    print("=" * 60)
    print("PortPilot Setup Parser Evaluation Benchmark")
    print("=" * 60)
    print(f"Execution Mode:       {report['mode'].upper()}")
    print(f"Provider Host:        {report['provider_host']}")
    print(f"Model Identifier:     {report['model']}")
    print(f"Cases Evaluated:      {report['total_cases']}")
    print(f"Exact Setup Matches:  {report['overall_exact_match_rate']:.1%}")
    print(f"Clarification Recall: {report['clarification']['recall']:.1%}")
    print(f"Unsupported Recall:   {report['unsupported']['recall']:.1%}")
    print("-" * 60)
    print("Per-Field Accuracy:")
    for field, data in report["fields"].items():
        print(f"  {field:20s}: {data['matched']:2d}/{data['total']:2d} ({data['accuracy']:.1%})")
    print("-" * 60)
    print(
        f"Latency: p50={report['latency_ms']['median']}ms, "
        f"p95={report['latency_ms']['p95']}ms, max={report['latency_ms']['max']}ms"
    )
    print(f"Failures: {report['failure_count']}")
    for f in report["failures"]:
        print(f"  - [{f['id']}] expected {f['expected']}, got {f['actual']}")
    print("=" * 60)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Saved JSON report: {args.output_json}")

    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(report), encoding="utf-8")
        print(f"Saved Markdown report: {args.output_md}")


if __name__ == "__main__":
    main()
