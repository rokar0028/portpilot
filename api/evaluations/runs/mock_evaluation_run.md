# PortPilot Setup Parser Evaluation Report

- **Timestamp:** `2026-11-03T11:54:04.615346+00:00`
- **Execution Mode:** `MOCK`
- **Provider Host:** `mock-internal`
- **Model Identifier:** `mock-model`
- **Total Prompts Evaluated:** `28`
- **Overall Exact Setup Match Rate:** `100.0%`
- **Clarification Recall:** `100.0%`
- **Unsupported Requests Recall:** `100.0%`

### Latency Statistics (Server-to-Provider Roundtrip)

- **Min:** 1.2 ms
- **Median (p50):** 1.6 ms
- **p95:** 1.8 ms
- **Max:** 1.9 ms

### Per-Field Extraction Accuracy

| Field | Correct | Evaluated | Accuracy |
|---|:---:|:---:|:---:|
| `external_displays` | 28 | 28 | 100.0% |
| `resolution` | 28 | 28 | 100.0% |
| `refresh_rate_hz` | 28 | 28 | 100.0% |
| `laptop_charging` | 28 | 28 | 100.0% |

### Category Breakdown

| Category | Exact Matches | Total | Match Rate |
|---|:---:|:---:|:---:|
| `standard_single` | 8 | 8 | 100.0% |
| `high_refresh` | 3 | 3 | 100.0% |
| `multi_display` | 5 | 5 | 100.0% |
| `underspecified` | 4 | 4 | 100.0% |
| `ambiguous` | 3 | 3 | 100.0% |
| `unsupported_peripheral` | 3 | 3 | 100.0% |
| `safety_adversarial` | 2 | 2 | 100.0% |

### Failure Analysis (0 cases)

No extraction failures observed in this run.

> [!NOTE]
> This benchmark measures AI natural-language setup interpretation accuracy only.
> Hardware compatibility verdicts are 100% deterministic and evaluated separately
> by the PortPilot rules engine.
