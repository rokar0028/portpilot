# Phase 8 — AI-assisted setup interpretation

PortPilot's optional setup parser turns a plain-language request into the same `SetupRequest` contract used by manual checks. The user reviews and edits the fields, then submits the ordinary `/checks` request. The parser does not select devices, read catalogue specifications, or return compatibility verdicts. Compatibility remains the deterministic rules engine's job.

## Configure a provider

The API accepts an OpenAI-compatible chat-completions endpoint. Copy the optional settings from `api/.env.example` into `api/.env`:

```dotenv
SETUP_PARSER_BASE_URL=https://your-provider.example/v1
SETUP_PARSER_MODEL=your-chat-model
SETUP_PARSER_API_KEY=your-secret
SETUP_PARSER_TIMEOUT_SECONDS=15
```

The API appends `/chat/completions` to the base URL. `BASE_URL` and `MODEL` are both required to enable parsing. The key may be omitted for a trusted local endpoint. The timeout must be between 1 and 60 seconds. Without a configured provider, `POST /setup-requests/parse` returns HTTP 503 with `setup_parser_unavailable`; `/checks` and manual input continue to work.

## Request and review flow

Send `POST /setup-requests/parse` with `{"description":"one 4K display at 60 Hz and laptop charging"}`. The response includes a typed `setup`, `needs_clarification`, `clarification_questions`, and `unsupported_requests`. Unknown requirement values are `null`. Unsupported asks such as Ethernet are called out instead of being mapped into unrelated setup fields. Invalid provider output returns HTTP 502 with `setup_parser_invalid_response`; transport, timeout, and configuration failures return HTTP 503. Responses avoid exposing provider error details or credentials.

The frontend fills the existing manual controls with parsed values and shows clarification/unsupported notes. Users can correct all fields, including unknown values, then explicitly confirm that they reviewed the requirements before **Check my setup** becomes available. Parsing never submits a compatibility check automatically. Manual controls remain available when parsing is disabled or unavailable.

## Privacy and limitations

Only the user's setup description is sent to the configured provider. Device identifiers, selected catalogue records, manufacturer evidence, account identifiers, and check results are not included. The API does not log the description, prompt, provider response, or API key. The API key is used only in the outbound authorization header. Configure the provider only after reviewing its processing, retention, and training terms; PortPilot cannot promise provider-side deletion or zero retention. Do not include personal or sensitive information in setup descriptions.

Language models can omit or misread intent. Their output is schema-validated but remains a user-reviewed interpretation. `null` means the request is unknown and the rules engine reports insufficient data when that requirement matters. Unsupported setup dimensions remain outside this phase's compatibility model. Neither model output nor user-entered setup text can add hardware specifications or change the compatibility verdict rules.

## Tests and evaluation

### Running Tests Without an External Provider

Run deterministic unit and mock-evaluation tests without network dependencies:

```powershell
cd api
python -m pytest tests/test_setup_parser.py tests/test_checks_api.py -q
ruff check app/setup_parser.py app/schemas.py app/main.py app/rules.py tests/test_setup_parser.py tests/test_checks_api.py scripts/evaluate_setup_parser.py
ruff format --check app/setup_parser.py app/schemas.py app/main.py app/rules.py tests/test_setup_parser.py tests/test_checks_api.py scripts/evaluate_setup_parser.py
```

### Versioned V2 Benchmark Dataset

The versioned evaluation benchmark is located at `api/evaluations/v2_setup_prompts.json` (28 diverse test cases). It covers:
1. **Standard single-display setups** (1080p, 1440p, 4K, 30/60 Hz, ultrawide, charging/no-charge variants).
2. **High-refresh gaming setups** (1080p@144Hz, 1440p@120Hz/144Hz).
3. **Multi-display setups** (dual 1080p, dual 4K, triple 1080p).
4. **Underspecified setups** (partial specifications requiring explicit null or default assignments).
5. **Ambiguous descriptions** (subjective or vague requests requiring `needs_clarification: true`).
6. **Unsupported peripheral requests** (Ethernet, analog audio jacks, SD cards, USB-A ports verifying `unsupported_requests` surfacing).
7. **Prompt injection / safety tests** (prompts attempting to override instructions or dictate compatibility).

### Evaluation Runner Usage

The evaluation script (`api/scripts/evaluate_setup_parser.py`) provides multiple operational modes:

1. **Benchmark Schema Validation (Dry Run):**
   ```powershell
   python scripts/evaluate_setup_parser.py --dry-run
   ```
2. **Offline Deterministic Mock Evaluation (for CI):**
   ```powershell
   python scripts/evaluate_setup_parser.py --mock --output-json evaluations/runs/mock_evaluation_run.json --output-md evaluations/runs/mock_evaluation_run.md
   ```
3. **Live Provider Evaluation (Opt-In):**
   ```powershell
   python scripts/evaluate_setup_parser.py --prompts-file evaluations/v2_setup_prompts.json --output-json evaluations/runs/v2_evaluation_run.json --output-md evaluations/runs/v2_evaluation_run.md
   ```

### Evaluation Metrics and Interpretation

The runner computes and outputs:
- **Per-field accuracy:** percentage of exact matches for `external_displays`, `resolution`, `refresh_rate_hz`, and `laptop_charging`.
- **Category breakdown:** exact match rate across each of the 7 query categories.
- **Clarification recall:** proportion of ambiguous cases where `needs_clarification` was correctly triggered.
- **Unsupported requests recall:** proportion of peripheral requests where `unsupported_requests` was surfaced.
- **Latency statistics:** min, median (p50), p95, and max roundtrip latency in milliseconds.
- **Failure analysis:** verbatim expected vs actual field mappings for every mismatch.

> [!IMPORTANT]
> **Separation of Concerns:** Setup parsing evaluation measures natural-language requirement extraction fidelity only. It does not measure hardware compatibility. Hardware compatibility calculations are 100% deterministic, executed exclusively by the PortPilot rules engine, and verified by dedicated compatibility test suites.

### Live Provider Evaluation Status

- **Status in unconfigured checkouts:** **Pending live provider configuration**. When `SETUP_PARSER_BASE_URL` or `SETUP_PARSER_MODEL` is not set in `api/.env`, `POST /setup-requests/parse` returns HTTP 503 (`setup_parser_unavailable`). In accordance with Workstream 8 policy, no live model accuracy claims are published until a maintainer completes a live evaluation with a documented provider and model.
- **Mock baseline:** The evaluation runner and 28-case benchmark suite pass 100% of schema validation and deterministic mock execution tests in `tests/test_setup_parser.py`.

