import { expect, test, type Page } from "@playwright/test";

const apiOrigin = process.env.PORTPILOT_E2E_API_URL ?? "http://127.0.0.1:18000";

async function selectDefaultDevices(page: Page) {
  await page.goto("/");
  await expect(page.getByLabel("Your laptop", { exact: true })).toBeEnabled();
  await page
    .getByLabel("Your laptop", { exact: true })
    .selectOption({ index: 1 });
  await page.locator("#accessory").selectOption({ index: 1 });
}

test.describe("Screen-Reader & ARIA Contract Test Suite (WS-6)", () => {
  test("Scenario 1: Open and select devices — landmarks, accessible names, model codes, and disclosures", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByLabel("Your laptop", { exact: true })).toBeEnabled();

    // 1. Heading hierarchy and landmark structure
    await expect(page.locator("main")).toBeVisible();
    const mainHeading = page.getByRole("heading", { level: 1 });
    await expect(mainHeading).toContainText(/will your (gear|devices)/i);

    // 2. Form controls have explicit accessible labels
    const laptopSelect = page.getByLabel("Your laptop", { exact: true });
    await expect(laptopSelect).toHaveAttribute("id", "laptop");

    const accessorySelect = page.getByRole("combobox", {
      name: "Connect a dock, hub or charger",
    });
    await expect(accessorySelect).toHaveAttribute("id", "accessory");

    // 3. Option text distinguishes exact models and model codes
    const laptopOptions = await page
      .locator("#laptop option")
      .allTextContents();
    // Non-placeholder options must contain model codes in parentheses
    const validLaptopOptions = laptopOptions.filter(
      (opt) => !opt.toLowerCase().includes("choose") && opt.trim().length > 0,
    );
    expect(validLaptopOptions.length).toBeGreaterThan(0);
    for (const opt of validLaptopOptions) {
      expect(opt).toMatch(/(·\s*|\()[A-Z0-9-]+/i);
    }

    // 4. Select devices and inspect verified details disclosure
    await laptopSelect.selectOption({ index: 1 });
    await accessorySelect.selectOption({ index: 1 });

    const laptopDetails = page
      .locator(".selected-device-summary details")
      .first();
    if (await laptopDetails.count()) {
      await expect(laptopDetails.locator("summary")).toBeVisible();
      await laptopDetails.locator("summary").click();
      await expect(laptopDetails).toHaveAttribute("open", "");
    }
  });

  test("Scenario 2: Setup fields and parsed setup review — names, live announcements, and review contract", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByLabel("Your laptop", { exact: true })).toBeEnabled();

    // 1. Open setup disclosure and verify accessible names on all inputs
    const setupDisclosure = page.getByText("Adjust screen or charging needs", {
      exact: true,
    });
    await expect(setupDisclosure).toBeVisible();
    await setupDisclosure.click();

    await expect(
      page.getByLabel("Describe your setup (optional)"),
    ).toBeVisible();
    await expect(page.getByLabel("External screens")).toBeVisible();
    await expect(page.getByLabel("Resolution")).toBeVisible();
    await expect(page.getByLabel("Refresh")).toBeVisible();
    await expect(
      page.getByRole("combobox", {
        name: /^(Laptop charging|Charge laptop)/i,
      }),
    ).toBeVisible();

    // 2. Natural language setup interpretation with mock API response
    await page.route("**/setup-requests/parse", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          setup: {
            external_displays: 1,
            resolution: "3840x2160",
            refresh_rate_hz: 60,
            laptop_charging: true,
          },
          needs_clarification: false,
          clarification_questions: [],
          unsupported_requests: [],
          notice:
            "Review extracted fields before running the compatibility check.",
        }),
      }),
    );

    await page
      .getByLabel("Describe your setup (optional)")
      .fill("Dual 4K displays at 60 Hz with charging");
    await page.getByRole("button", { name: "Interpret setup" }).click();

    // 3. ARIA live region announces completion
    const statusLiveRegion = page.locator(
      '.sr-only[role="status"][aria-live="polite"]',
    );
    await expect(statusLiveRegion).toContainText(
      "Setup interpreted. Review the extracted requirements and confirm them before checking.",
    );

    // 4. Review confirmation contract enforces checking blockage until confirmed
    const reviewCheckbox = page.getByRole("checkbox", {
      name: /I reviewed these requirements/i,
    });
    await expect(reviewCheckbox).toBeVisible();
    await expect(reviewCheckbox).not.toBeChecked();

    // Select laptop and accessory
    await page
      .getByLabel("Your laptop", { exact: true })
      .selectOption({ index: 1 });
    await page.locator("#accessory").selectOption({ index: 1 });

    const checkButton = page.getByRole("button", { name: /check my setup/i });
    // Button must be disabled until user confirms review
    await expect(checkButton).toBeDisabled();

    // Confirm review -> button becomes enabled
    await reviewCheckbox.check();
    await expect(checkButton).toBeEnabled();

    // 5. Changing any setup field invalidates review and requires re-confirmation
    await page.getByLabel("Resolution").selectOption("1920x1080");
    await expect(reviewCheckbox).not.toBeChecked();
    await expect(checkButton).toBeDisabled();
  });

  test("Scenario 3: Error alerts and resilience announcements — catalogue outage and service errors", async ({
    page,
  }) => {
    // 1. Catalogue outage simulation
    await page.route("**/devices", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Catalogue temporarily offline" }),
      }),
    );
    await page.goto("/");

    const catalogErrorAlert = page.locator('.catalog-error[role="alert"]');
    await expect(catalogErrorAlert).toBeVisible();
    await expect(catalogErrorAlert).toContainText(
      "We couldn’t load the device list.",
    );

    const retryButton = catalogErrorAlert.getByRole("button", {
      name: /try again/i,
    });
    await expect(retryButton).toBeVisible();
    await expect(retryButton).toBeEnabled();

    // Unroute catalogue error and recover
    await page.unroute("**/devices");
    await retryButton.click();
    await expect(page.getByLabel("Your laptop", { exact: true })).toBeEnabled();
    await expect(catalogErrorAlert).not.toBeVisible();

    // 2. Compatibility service failure simulation
    await page
      .getByLabel("Your laptop", { exact: true })
      .selectOption({ index: 1 });
    await page.locator("#accessory").selectOption({ index: 1 });

    await page.route("**/checks", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Check service unavailable" }),
      }),
    );

    const submitBtn = page.getByRole("button", { name: /check my setup/i });
    await submitBtn.click();

    const formErrorAlert = page.locator('.form-error[role="alert"]');
    await expect(formErrorAlert).toBeVisible();
    await expect(formErrorAlert).toContainText(
      "The compatibility service could not complete this check.",
    );
    // Submit button remains available for retry
    await expect(submitBtn).toBeEnabled();
  });

  test("Scenario 4: Result announcements, heading hierarchy, and aria-hidden icon contracts", async ({
    page,
  }) => {
    await selectDefaultDevices(page);

    // Mock a compatible_with_limits result
    await page.route("**/checks", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          verdict: "compatible_with_limits",
          summary:
            "Supports single 4K at 60 Hz, but secondary monitor is limited to 30 Hz.",
          limits: [
            "DisplayPort 1.2 alt-mode bandwidth restricts dual 4K monitors to 30 Hz.",
          ],
          requirements: [
            {
              name: "Video Output",
              status: "passed",
              detail: "DisplayPort Alt Mode supported by laptop.",
            },
            {
              name: "Display Bandwidth",
              status: "passed",
              detail: "Single display up to 4K 60Hz supported.",
            },
          ],
          evidence: [
            {
              id: "ev-1",
              title: "Manufacturer Hardware Specification",
              url: "https://example.invalid/specs",
              excerpt: "Supports DP 1.2 alt mode via USB-C port.",
            },
          ],
          rule_engine_version: "0.3.0",
        }),
      }),
    );

    await page.getByRole("button", { name: /check my setup/i }).click();

    // 1. ARIA Live region announces completion, verdict heading, and summary
    const statusLiveRegion = page.locator(
      '.sr-only[role="status"][aria-live="polite"]',
    );
    await expect(statusLiveRegion).toContainText("Check complete.");
    await expect(statusLiveRegion).toContainText("Works with limits.");
    await expect(statusLiveRegion).toContainText(
      "Supports single 4K at 60 Hz, but secondary monitor is limited to 30 Hz.",
    );

    // 2. Result heading hierarchy: h2.verdict-title appears under h1
    const verdictHeading = page.locator("h2.verdict-title");
    await expect(verdictHeading).toBeVisible();
    await expect(verdictHeading).toHaveText("Works with limits");

    // 3. Known limitations callout has accessible region and list
    const limitRegion = page.getByRole("region", {
      name: "Hardware limitations and constraints",
    });
    await expect(limitRegion).toBeVisible();
    await expect(
      limitRegion.getByText("Hardware constraints & limitations"),
    ).toBeVisible();
    const limitList = page.locator(
      'ul.limit-list[aria-label="Known limitations"]',
    );
    await expect(limitList).toBeVisible();
    await expect(limitList.locator("li")).toHaveCount(1);

    // 4. Icons have aria-hidden="true" to prevent redundant screen reader speech
    const verdictIcon = page.locator(".verdict-icon");
    await expect(verdictIcon).toHaveAttribute("aria-hidden", "true");

    const deviceArrow = page.locator(".device-pair span[aria-hidden='true']");
    await expect(deviceArrow).toBeVisible();

    // 5. Modifying selection clears stale result from the accessibility tree
    await page.locator("#accessory").selectOption({ index: 2 });
    await expect(page.locator(".empty-result")).toBeVisible();
    await expect(page.locator("h2.verdict-title")).not.toBeVisible();
  });

  test("Scenario 5: Report submission and responsive keyboard focus management (360px viewport)", async ({
    page,
  }) => {
    await selectDefaultDevices(page);

    // Mock check response
    await page.route("**/checks", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          verdict: "compatible",
          summary: "Fully compatible.",
          limits: [],
          requirements: [
            {
              name: "Power Delivery",
              status: "passed",
              detail: "Hub provides 65W pass-through.",
            },
          ],
          evidence: [],
          rule_engine_version: "0.3.0",
        }),
      }),
    );
    await page.getByRole("button", { name: /check my setup/i }).click();
    await expect(page.locator("h2.verdict-title")).toBeVisible();

    // 1. Result inaccuracy report disclosure and submission
    const reportDisclosure = page.locator("details.result-report");
    await expect(reportDisclosure).toBeVisible();
    await reportDisclosure.locator("summary").click();

    await expect(page.getByLabel("What seems wrong? (optional)")).toBeVisible();

    await page.route("**/result-reports", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "received" }),
      }),
    );

    await page
      .getByLabel("What seems wrong? (optional)")
      .fill("My external display was unable to wake from sleep with this hub.");
    await page.getByRole("button", { name: "Send report" }).click();

    // Report status confirmation announced
    const reportStatus = page.locator(".result-report p[role='status']");
    await expect(reportStatus).toContainText(
      "Thanks. Your report was sent to the PortPilot team.",
    );

    // 2. Responsive 360px viewport keyboard navigation
    await page.setViewportSize({ width: 360, height: 800 });
    await page.goto("/");
    await expect(page.getByLabel("Your laptop", { exact: true })).toBeEnabled();

    // Verify sequential keyboard tab stops receive focus
    let activeElements = 0;
    for (let i = 0; i < 8; i += 1) {
      await page.keyboard.press("Tab");
      const activeTag = await page.evaluate(
        () => document.activeElement?.tagName,
      );
      if (
        activeTag &&
        ["A", "BUTTON", "SELECT", "INPUT", "TEXTAREA", "SUMMARY"].includes(
          activeTag,
        )
      ) {
        activeElements += 1;
      }
    }
    expect(activeElements).toBeGreaterThan(0);

    // Confirm zero horizontal scrollbar overflow at 360px
    const dimensions = await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      content: document.documentElement.scrollWidth,
    }));
    expect(dimensions.content).toBeLessThanOrEqual(dimensions.viewport);
  });

  test("Scenario 6: Insufficient data breakdown — missing specifications breakdown region and unverified requirements list", async ({
    page,
  }) => {
    await selectDefaultDevices(page);

    // Mock an insufficient_data result with unverified requirements
    await page.route("**/checks", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          verdict: "insufficient_data",
          summary:
            "We could not confirm if this hub works because laptop video mode is unverified.",
          limits: [],
          requirements: [
            {
              name: "USB-C Video Output",
              status: "unknown",
              detail:
                "DisplayPort Alt Mode specification has not been verified from manufacturer documentation.",
            },
            {
              name: "Charging Compatibility",
              status: "passed",
              detail: "Pass-through charging power is adequate.",
            },
          ],
          evidence: [],
          rule_engine_version: "0.4.0",
        }),
      }),
    );

    await page.getByRole("button", { name: /check my setup/i }).click();

    // 1. Result heading indicates insufficient data
    const verdictHeading = page.locator("h2.verdict-title");
    await expect(verdictHeading).toBeVisible();
    await expect(verdictHeading).toHaveText("Not enough information");

    // 2. Missing specifications breakdown region is rendered with heading
    const missingDataRegion = page.getByRole("region", {
      name: "Missing specifications breakdown",
    });
    await expect(missingDataRegion).toBeVisible();
    await expect(
      missingDataRegion.getByText("What manufacturer data is missing?"),
    ).toBeVisible();

    // 3. Unverified requirements list contains the unverified item
    const unverifiedList = page.getByRole("list", {
      name: "Unverified requirements",
    });
    await expect(unverifiedList).toBeVisible();
    await expect(unverifiedList.locator("li")).toHaveCount(1);
    await expect(unverifiedList).toContainText("USB-C Video Output");
    await expect(unverifiedList).toContainText(
      "DisplayPort Alt Mode specification has not been verified",
    );
  });
});
