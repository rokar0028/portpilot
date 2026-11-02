# PortPilot implementation plan

## 1. Product decision

**PortPilot** answers a narrow, expensive question before someone buys or opens a laptop accessory:

> Will this laptop work with this dock, monitor, hub, charger, or portable monitor for my setup?

The first release is an explainable compatibility checker. It uses structured specifications and deterministic rules. AI may make the explanation easier to read, but it must never be the source of the compatibility verdict.

### Target user

A student or working professional with a Windows laptop who wants to connect a monitor, dock, USB-C hub, charger, or portable monitor and does not understand USB-C, Power Delivery, DisplayPort Alt Mode, USB4, or Thunderbolt.

### Success criterion for the first release

For every supported laptop and accessory pair, PortPilot returns one of these outcomes with evidence:

- **Compatible** — the requested setup is supported.
- **Compatible with limits** — it works, but with an explicit limitation such as one monitor, a lower refresh rate, or no charging.
- **Incompatible** — a necessary capability is absent.
- **Insufficient data** — the public specifications are incomplete; PortPilot does not guess.

## 2. Scope boundaries

### Release 1 includes

- Compatibility between one laptop and one accessory.
- Four accessory categories: USB-C hubs/docks, portable monitors, USB-C chargers, and external displays.
- A small curated catalogue: 30 laptops and 30 accessories.
- Windows laptops first; macOS support only where manufacturer documentation is clear.
- One requested setup: charging, one external monitor, two monitors, USB devices, Ethernet, or a portable monitor.
- Public source links attached to every catalogued capability.

### Release 1 excludes

- Marketplace listings, affiliate links, prices, stock, and payments.
- Scraping retailer pages as a source of truth.
- Claims based on unverified community reports.
- Universal support for every laptop or accessory.
- Hardware diagnosis after a purchase.
- Automatic product recommendations from live ecommerce data.

These boundaries keep the project credible and possible to complete alone.

## 3. Differentiation

Compatibility checkers already exist. PortPilot should compete on **clarity**, not an unrealistic claim to cover every device.

1. Explain the verdict in plain English.
2. Show exactly which laptop and accessory features were compared.
3. Cite the manufacturer documentation used for each input.
4. Focus on common, affordable setups used by Indian students and professionals.
5. Prefer an honest “insufficient data” response to a confident but unreliable answer.

## 4. Technical design

### Suggested stack

- **Frontend:** Next.js, TypeScript, Tailwind CSS.
- **Backend:** FastAPI, Python 3.12.
- **Database:** PostgreSQL with SQLAlchemy and Alembic migrations.
- **Authentication:** none for public checking in Release 1; a simple password-protected admin route for catalogue editing.
- **Deployment:** Vercel for the frontend and Render/Railway/Fly.io for API and PostgreSQL, or Docker Compose locally.
- **Testing:** pytest for the compatibility engine; Playwright for the principal user journey.

This gives you a genuinely full-stack project while keeping the critical reasoning engine in Python, where you already have experience from SSCRE.

### Architecture

```text
User selects laptop + accessory + intended setup
                |
                v
Next.js web app -----> FastAPI API -----> PostgreSQL catalogue
                              |
                              v
                    deterministic rule engine
                              |
                              v
           verdict + limits + evidence + plain-English explanation
```

### Main entities

**LaptopModel**

- brand, model name, region/model code, operating system
- USB-C port capabilities: data speed, DP Alt Mode, USB4/Thunderbolt version, Power Delivery input
- HDMI/DisplayPort capabilities
- maximum native external displays and documented limitations
- source URL, source excerpt, verification date, confidence

**AccessoryModel**

- brand, model name, category
- upstream connection requirement
- required host capabilities
- Power Delivery output
- display outputs and stated display modes
- USB, Ethernet, and card-reader capabilities
- source URL, source excerpt, verification date, confidence

**CompatibilityCheck**

- laptop, accessory, intended setup
- verdict, limitations, failed requirements, warnings
- rule engine version and generated timestamp

### Compatibility rules for Release 1

Implement rules as small, independently tested functions. Each rule returns a result and an explanation.

1. **Physical connection:** matching port or a supported adapter path exists.
2. **Video output:** the laptop provides HDMI or a USB-C video standard required by the accessory.
3. **Display count:** requested displays do not exceed the laptop’s documented native limit.
4. **Display mode:** required resolution and refresh rate fit the declared laptop, dock, and monitor limits.
5. **Charging:** the accessory provides enough Power Delivery for the laptop’s expected charging requirement; explain that it may charge slowly where exact demand is unknown.
6. **USB bandwidth:** warn when a display configuration consumes lanes or bandwidth that constrains storage or peripheral performance.
7. **Operating-system constraint:** surface documented macOS/Windows limitations rather than silently treating systems as equivalent.
8. **Evidence completeness:** return `insufficient_data` if any required fact is absent.

## 5. Catalogue acquisition plan

Do not begin with web scraping. Build a small, high-quality source catalogue manually from official manuals and specification pages.

### Initial laptop families

- Lenovo IdeaPad Slim and ThinkPad
- HP Pavilion and Victus
- ASUS VivoBook and TUF
- Acer Aspire and Nitro
- Dell Inspiron and Latitude

Choose exact models only after their official technical manuals have enough port and display information. A model family name alone is not precise enough.

### Initial accessories

- USB-C hubs from UGREEN, Anker, Portronics, Belkin, and Dell
- portable monitors from Lenovo, ASUS, and one budget manufacturer with complete specifications
- USB-C chargers at 45 W, 65 W, and 100 W
- common 1080p and 4K monitors with HDMI or USB-C input

For every record, preserve the source URL, a short quotation or factual excerpt, and the date it was checked. This turns catalogue maintenance into a visible engineering feature.

## 6. Seven-phase delivery plan

### Phase 1 — project foundation

- [ ] Create a Git repository and a concise README containing the problem, scope, and limitations.
- [ ] Set up the Next.js frontend and FastAPI backend as separate applications.
- [ ] Add Docker Compose for local development.
- [ ] Configure formatting, linting, environment variables, and a basic CI workflow.

**Completion:** both applications start locally and the README gives another developer clear setup steps.

### Phase 2 — catalogue and evidence model

- [ ] Create PostgreSQL tables and migrations for laptops, accessories, source evidence, and compatibility checks.
- [ ] Define Pydantic schemas for every public API request and response.
- [ ] Add source URL, factual excerpt, verification date, and confidence to every catalogue record.
- [ ] Enter five laptops and five accessories from official technical documentation.

**Completion:** the API can return a complete, evidence-backed record for every seed item.

### Phase 3 — compatibility rules engine

- [ ] Implement physical-connection compatibility checks.
- [ ] Implement video-output and DisplayPort Alt Mode checks.
- [ ] Implement display-count and resolution/refresh-rate checks.
- [ ] Implement Power Delivery and charging-limit checks.
- [ ] Return `insufficient_data` when a required capability is unknown.
- [ ] Write at least 20 unit tests for compatible, limited, incompatible, and uncertain cases.

**Completion:** `POST /checks` returns a deterministic verdict with reasons for the seed catalogue.

### Phase 4 — catalogue management

- [ ] Build a protected admin page or API for adding and editing laptops and accessories.
- [ ] Validate required specification fields before publishing a catalogue record.
- [ ] Add a source-review status: draft, verified, or needs review.
- [ ] Expand the catalogue to 15 laptops and 15 accessories with official sources.
- [ ] Add test fixtures for known limitations and missing-specification cases.

**Completion:** you can update the catalogue without editing database rows manually.

### Phase 5 — user experience

- [ ] Build the selector flow: laptop → accessory → intended setup.
- [ ] Create a result page that prioritises the verdict and plain-English explanation.
- [ ] Show which rules passed, failed, or could not be verified.
- [ ] Add a short glossary for USB-C, DP Alt Mode, Power Delivery, USB4, and Thunderbolt.
- [ ] Add shareable result URLs.

**Completion:** a nontechnical user can complete a compatibility check in under one minute.

### Phase 6 — quality and expansion

- [ ] Expand to 30 laptops and 30 accessories only where official evidence is complete.
- [ ] Add at least 50 compatibility-engine tests.
- [ ] Test the main browser journey on desktop and mobile.
- [ ] Create a public coverage and limitations page.
- [ ] Review every “compatible” verdict to confirm that no required fact is missing.

**Completion:** the app is trustworthy within its declared catalogue and refuses to guess outside it.

### Phase 7 — deployment and portfolio release

- [ ] Deploy the frontend, API, and database.
- [ ] Add monitoring for API errors and failed compatibility checks.
- [ ] Add architecture, design choices, test count, sources policy, and limitations to the README.
- [ ] Record a 90-second demo showing one compatible and one incompatible setup.
- [ ] Add the live link, source repository link, and demo video to your portfolio.

**Completion:** a recruiter can understand the project, run it, and see a credible live demonstration.

## 7. What makes this impressive in interviews

The talking point is not “I built another product finder.” It is:

> I built an explainable compatibility system. Its answers come from an auditable rules engine and cited manufacturer specifications; when the evidence is incomplete, it tells the user instead of guessing.

This connects naturally to SSCRE’s conservative decision-making. SSCRE fails closed for unsafe semantic reuse; PortPilot fails closed for incomplete hardware evidence. The projects are related in engineering judgment but solve very different user problems.

## 8. Acceptance checklist

- [ ] A user can complete one check in under one minute.
- [ ] Every non-trivial verdict lists the relevant evidence and failed or satisfied rules.
- [ ] The system never returns “compatible” when a required capability is unknown.
- [ ] At least 50 scenario tests cover the compatibility engine.
- [ ] The catalogue contains 30 laptops and 30 accessories with official sources.
- [ ] The public README includes setup steps, architecture, supported scope, and known limitations.
- [ ] A live demo and short video demonstrate one compatible and one incompatible setup.

## 9. First task

Create the repository and implement a tiny vertical slice before designing the full interface:

1. Add one laptop: a model with documented USB-C video and charging capabilities.
2. Add one USB-C hub with HDMI and Power Delivery pass-through.
3. Implement a check for one 1080p external monitor plus charging.
4. Return the verdict, reasons, and documentation links.
5. Write tests for one compatible, one incompatible, and one insufficient-data case.

Once this is done, every later feature extends a working, testable product instead of a mock-up.
