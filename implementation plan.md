# PortPilot — Phase 0 Implementation Plan

## Goal

Turn the PortPilot concept into a small, testable build specification before starting the seven delivery phases. Phase 0 ends with clear product boundaries, technical decisions, and a first vertical slice that can be implemented in Phase 1–3.

## In scope

- Confirm the first-release user, problem, and supported compatibility outcomes.
- Choose the initial laptop and accessory use case for the vertical slice.
- Define the minimum data and API contract needed by the rules engine.
- Establish the evidence policy for catalogued specifications.
- Convert open decisions into a sequenced implementation backlog.

## Work plan

### 1. Lock the first-release scope

- [ ] Keep the first release focused on a Windows laptop paired with one accessory and one requested setup.
- [ ] Confirm the four supported accessory categories: USB-C hubs/docks, portable monitors, USB-C chargers, and external displays.
- [ ] Keep the four verdicts: `compatible`, `compatible_with_limits`, `incompatible`, and `insufficient_data`.
- [ ] Record exclusions: retailer scraping, prices and stock, unverified community claims, and unsupported devices.

**Output:** a short scope section in the project README or product brief, consistent with the existing PortPilot plan.

### 2. Choose the vertical-slice scenario

- [ ] Select one exact laptop model and regional model code with official documentation.
- [ ] Select one USB-C hub with HDMI and Power Delivery pass-through, also with official documentation.
- [ ] Define the requested setup as one 1080p external monitor plus laptop charging.
- [ ] Identify one documented compatible, one incompatible, and one missing-evidence case for later rule-engine tests.

**Output:** a one-page scenario brief with device identifiers, intended setup, expected outcome, and source URLs. Do not assert a verdict until the relevant specifications are verified.

### 3. Set the evidence rules

- [ ] Use manufacturer manuals or specification pages as the source of truth.
- [ ] For each capability, record its source URL, relevant excerpt, checked date, and verification status.
- [ ] Treat unknown required capabilities as unknown; the engine must return `insufficient_data` rather than infer support.
- [ ] Define a lightweight review status such as `draft`, `verified`, or `needs_review`.

**Output:** an evidence-record template and a written rule for when a catalog item is considered verified.

### 4. Specify the smallest data and API contract

- [ ] List the laptop facts required for the vertical slice: connection type, video capability, supported display mode, charging input details, and evidence.
- [ ] List the accessory facts required: host connection requirements, HDMI mode, Power Delivery output, and evidence.
- [ ] Define the check request: laptop ID, accessory ID, and requested setup.
- [ ] Define the response: verdict, explanation, limits, unmet or unknown requirements, evidence references, and rule-engine version.
- [ ] Keep fields nullable or explicitly unknown where manufacturer documentation does not provide them.

**Output:** a brief schema/API note that can be translated into Pydantic and database models without inventing missing specifications.

### 5. Record implementation decisions and backlog

- [ ] Confirm the proposed stack: Next.js/TypeScript, FastAPI/Python, PostgreSQL, and Docker Compose for local development.
- [ ] Record any change to the proposed stack and the reason for it.
- [ ] Break the vertical slice into repository setup, evidence-backed seed data, deterministic rules, API response, and tests.
- [ ] Place broader catalogue entry, admin tools, interface polish, and deployment in the later phases already defined in the PortPilot plan.

**Output:** a prioritized Phase 1–3 backlog with dependencies and a clear first task.

## Phase 0 acceptance criteria

- [ ] The first-release scope and exclusions are written down and internally consistent.
- [ ] The vertical-slice devices are identified by exact model and have official source links, or the selection is explicitly marked as blocked on sourcing.
- [ ] Evidence fields and the “do not guess” policy are defined.
- [ ] The minimum request, response, and data fields for the vertical slice are documented.
- [ ] Technical decisions and the next implementation tasks are recorded.
- [ ] No compatibility verdict is presented as verified without supporting manufacturer evidence.

## Exit condition

Phase 0 is complete when another developer can begin Phase 1 and implement the vertical slice without needing to decide product scope, evidence standards, or the shape of the compatibility response. Move unresolved device sourcing into a tracked task rather than filling gaps with assumptions.
