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

Run focused deterministic tests without a provider:

```powershell
cd api
python -m pytest tests/test_setup_parser.py tests/test_checks_api.py -q
ruff check app/setup_parser.py app/schemas.py app/main.py app/rules.py tests/test_setup_parser.py tests/test_checks_api.py scripts/evaluate_setup_parser.py
ruff format --check app/setup_parser.py app/schemas.py app/main.py app/rules.py tests/test_setup_parser.py tests/test_checks_api.py scripts/evaluate_setup_parser.py
```

The five-case prompt set is `api/evaluations/phase8_setup_prompts.json`. To evaluate a live configured model, run `python scripts/evaluate_setup_parser.py` from `api`. This sends those prompts to the configured provider and reports exact field matches, clarification behavior, and failures. It is an opt-in parsing evaluation, not a compatibility evaluation. Results vary by provider/model and are not run as part of deterministic tests. Report per-field denominators and retain mismatches when sharing results; do not describe this small set as a general accuracy guarantee.

### Initial evaluation report

Status: **not run against a live provider**. No provider is configured in this checkout. The five prompts cover direct requirements, explicit no-charge intent, underspecification, ambiguity, and an unsupported Ethernet request. Field-level live accuracy is therefore not yet measured. The deterministic mocked tests verify contract extraction, null/clarification handling, unsupported-field surfacing, invalid response rejection, provider unavailability, and that only the user's description is included in provider input.
