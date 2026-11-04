# V2 Workstream 11 implementation plan

## Goal

Enhance hardware protocol fidelity, physical bus constraint modeling (macOS MST vs. SST limitations, DisplayPort lane bifurcation trade-offs, net Power Delivery pass-through margins), high-impact device coverage, and UI diagnostic transparency directly within the PortPilot repository.

## Problem statement & real-world context

In real-world computing, general-purpose LLMs and e-commerce listings produce frequent false positives because they ignore physical bus and operating system protocol constraints:
1. **macOS DisplayPort MST vs. SST**: macOS does not natively support DisplayPort Multi-Stream Transport (MST). Dual external displays plugged into a standard USB-C Alt Mode hub mirror rather than extend, unless using Thunderbolt or DisplayLink.
2. **High-Speed USB-C Lane Bifurcation**: A standard USB-C cable contains 4 high-speed differential pairs. A USB-C hub offering USB 3.0 (5 Gbps+) ports must allocate 2 lanes to USB data, leaving only 2 lanes for DisplayPort. On a DisplayPort 1.2 host (HBR2), 2 lanes cannot carry 4K@60Hz without Display Stream Compression (DSC), causing displays to drop to 4K@30Hz or 1080p@60Hz.
3. **Net Power Delivery Pass-Through Margins**: Hubs consume internal operating power (typically 15W). A 65W charger into a 15W-reservation hub only provides 50W to the laptop. If the laptop has a strict 65W minimum (`usb_c_pd_input_min_w`), charging fails.
4. **Catalogue Depth for Tricky Devices**: High-volume, confusing hardware (Apple Silicon MacBooks, Dell XPS, Lenovo ThinkPads, Dell WD-series docks) requires verified manufacturer evidence to prevent blind spots.
5. **UI Transparency**: Users need to see why an outcome is "Insufficient data" or "Compatible with limits" with clear step-by-step physical breakdown cards.

## Scope

### 1. Deterministic rules engine enhancements (`api/app/rules.py`)
- **macOS MST check**: When `laptop.operating_system` is macOS and the user requests $\ge 2$ extended displays via an accessory whose host connection is USB-C (non-Thunderbolt), evaluate as `incompatible` or `compatible_with_limits` with an explicit reason: "macOS does not support DisplayPort Multi-Stream Transport (MST); external displays will mirror unless connected via Thunderbolt or a native dual-bus dock."
- **Lane bifurcation & DP bandwidth calculation**: Model the 2-lane vs. 4-lane trade-off. When an accessory provides USB 3.0+ data ports alongside video without Thunderbolt, model 2-lane DP limits for DP 1.2 hosts.
- **Net charging pass-through margin**: Calculate net delivered power as $W_{\text{charger}} - W_{\text{hub\_overhead}}$ and verify against laptop minimum and maximum input wattages.

### 2. High-impact device catalogue expansion (`api/app/seed.py`)
- Add rigorously researched, verified manufacturer-evidenced records for high-frequency market hardware:
  - Apple MacBook Air / Pro (Apple Silicon M-series) with single/dual external display constraints.
  - Dell XPS 13 / 15 and Lenovo ThinkPad models.
  - Dell WD19S / WD22TB4 commercial docks.
  - Anker / Satechi multi-port hubs.
- Ensure all entries strictly adhere to the [Catalogue Identity and Evidence Standard](catalogue-identity-and-evidence.md) with exact model codes, checked dates, and manufacturer documentation URLs.

### 3. Frontend diagnostic breakdown & transparency (`web/src/app/page.tsx`)
- Enhance the verdict display to visually show the physical negotiation chain (Connector $\rightarrow$ Video Protocol $\rightarrow$ Display Topology $\rightarrow$ Power Budget).
- For `insufficient_data` results, display a dedicated card listing the specific missing manufacturer fields.

### 4. Code quality & CI hygiene
- Resolve all pending Ruff lint/format errors across `api/app` and `api/tests`.
- Ensure all existing and new test suites pass with 0 warnings and 100% verification across PostgreSQL and SQLite.

## Implementation steps

1. **Plan & Document**: Create this plan and link it from `docs/v2-implementation-plan.md` and `README.md`.
2. **Rules Engine Enhancements**:
   - Implement the macOS MST vs. SST topology check in `api/app/rules.py`.
   - Implement the net charging pass-through power margin calculation.
   - Implement lane bifurcation / DP 1.2 bandwidth warnings where applicable.
3. **Test Suite Expansion**:
   - Add unit tests in `api/tests/test_rules.py` covering macOS dual-monitor MST limits, net PD reservation math, and bandwidth constraints.
4. **Catalogue Expansion**:
   - Curate and verify new laptop and accessory seed records in `api/app/seed.py`.
5. **Code Health & Quality**:
   - Run `ruff format` and `ruff check --fix` across `api/`.
   - Run `pytest` to confirm full pass.
6. **Frontend Integration**:
   - Update `web/src/app/page.tsx` to surface detailed limit reasons and missing evidence summaries.

## Progress & status

- [x] Create this plan and link it from `docs/v2-implementation-plan.md` and `README.md`.
- [x] Implement the macOS DisplayPort MST vs. SST check in `api/app/rules.py`:
  - Extended multi-display requests over standard USB-C fail with an explicit limitation explaining that macOS does not support DisplayPort MST.
  - Mirrored multi-display requests pass with a documented limit explaining that displays will mirror.
  - Multi-display setups over Thunderbolt / USB4 correctly pass without MST penalties.
- [x] Implement high-speed lane bifurcation & DisplayPort 1.2 bandwidth constraint logic in `api/app/rules.py` (flagging 4K@60Hz over 2-lane DP 1.2 hubs).
- [x] Implement net Power Delivery pass-through margin calculation ($W_{\text{charger}} - W_{\text{hub\_reserve}}$) with explicit hub reservation explanations.
- [x] Bump `RULE_ENGINE_VERSION` to `0.4.0` and update API test assertions.
- [x] Update capability registry (`api/app/capabilities.py`) and `main.py` rule record adapters to keep registry validation clean.
- [x] Expand unit test suite with 5 new targeted test cases in `api/tests/test_rules.py` (total 129 tests passing).
- [x] Maintain 0 lint/format violations across Python (`ruff check`, `ruff format`) and Next.js (`eslint`, `prettier`, `next build`).
- [x] Expand verified catalogue with manufacturer-evidenced high-impact models:
  - Apple MacBook Air 13-inch (M2, Model A2681) capturing the 1 external display hardware limit.
  - Dell WD19S 130W USB-C Dock (Model K20A001) capturing DP 1.4, multi-display MST configurations, and 90W Dell / 65W generic PD.
  - Anker 555 USB-C Hub (8-in-1, Model A8383) capturing 100W PD input, 85W pass-through with 15W internal reservation, and 4K@60Hz HDMI.
- [x] Enhance frontend diagnostic presentation:
  - Styled `.limit-callout` hardware constraints container with distinct banner styling and screen-reader accessible region.
  - Interactive `.insufficient-data-box` breakdown detailing specific missing manufacturer specifications.
- [x] Implement browser E2E test coverage for new diagnostic UI in `web/e2e/accessibility-contracts.spec.ts` (Scenario 4 & Scenario 6) and `web/e2e/checker.spec.ts`.

## Acceptance criteria

- [x] macOS multi-display setups over standard USB-C DP Alt Mode correctly evaluate to `compatible_with_limits` (mirrored only) or `incompatible` for extended desktop requests.
- [x] Power delivery pass-through calculations account for accessory power draw overhead against laptop minimum required wattage.
- [x] Seeded high-impact, evidence-backed device models with verified manufacturer excerpts (19 laptops, 17 verified accessories).
- [x] Diagnostic UI enhancements render hardware limits callout and missing specification breakdowns with complete ARIA semantics.
- [x] All unit, integration, accessibility, and build checks pass without regressions (129 pytest tests, all 6 ARIA contract E2E scenarios, clean Next.js build).
- [x] API and frontend code passes `ruff check`, `ruff format --check`, `eslint`, and `prettier --check` cleanly with 0 errors.
