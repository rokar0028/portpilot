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

## Acceptance criteria

- [ ] macOS multi-display setups over standard USB-C DP Alt Mode correctly evaluate to `compatible_with_limits` (mirrored only) or `incompatible` for extended desktop requests.
- [ ] Power delivery pass-through calculations account for accessory power draw overhead against laptop minimum required wattage.
- [ ] At least 4 new high-impact, evidence-backed device models are seeded with verified manufacturer excerpts.
- [ ] All unit, integration, and E2E tests pass without regressions.
- [ ] API code passes `ruff check` and `ruff format --check` cleanly with 0 errors.
