import { expect, test, type Page } from "@playwright/test";

const apiOrigin = process.env.PORTPILOT_E2E_API_URL ?? "http://127.0.0.1:18000";

const laptopFixtureIds: Record<string, string> = {
  "E2E Supported Laptop": "e2e-good-laptop",
  "E2E No Video Laptop": "e2e-bad-laptop",
  "E2E Unknown Mode Laptop": "e2e-unknown-laptop",
};

const setupFieldsOpened = new WeakSet<Page>();

async function openSetupFields(page: Page) {
  if (setupFieldsOpened.has(page)) return;
  const setupDisclosure = page.getByText("Adjust screen or charging needs", {
    exact: true,
  });
  if (await setupDisclosure.count()) await setupDisclosure.click();
  setupFieldsOpened.add(page);
}

async function setLaptopCharging(page: Page, charging: boolean) {
  const select = page.getByRole("combobox", {
    name: /^(Laptop charging|Charge laptop)/i,
  });
  if (await select.count()) {
    await select.selectOption(String(charging));
    return;
  }

  const checkbox = page.getByRole("checkbox", {
    name: /charge my laptop through this accessory/i,
  });
  if (charging) await checkbox.check();
  else await checkbox.uncheck();
}

async function expectLaptopCharging(page: Page, charging: boolean) {
  const select = page.getByRole("combobox", {
    name: /^(Laptop charging|Charge laptop)/i,
  });
  if (await select.count()) {
    await expect(select).toHaveValue(String(charging));
    return;
  }

  const checkbox = page.getByRole("checkbox", {
    name: /charge my laptop through this accessory/i,
  });
  if (charging) await expect(checkbox).toBeChecked();
  else await expect(checkbox).not.toBeChecked();
}

async function chooseFixture(page: Page, laptop = "E2E Supported Laptop") {
  await page
    .getByLabel("Your laptop", { exact: true })
    .selectOption(laptopFixtureIds[laptop]);
  await page
    .getByRole("combobox", { name: "Connect a dock, hub or charger" })
    .selectOption("e2e-good-hub");
}

async function submitSupportedCheck(page: Page) {
  await chooseFixture(page);
  await openSetupFields(page);
  await setLaptopCharging(page, false);
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(
    page.getByRole("heading", { name: /compatible/i }),
  ).toBeVisible();
}

async function changeSelect(page: Page, label: string) {
  if (label === "Laptop charging") {
    const select = page.getByRole("combobox", {
      name: /^(Laptop charging|Charge laptop)/i,
    });
    if (await select.count()) {
      await setLaptopCharging(page, (await select.inputValue()) !== "true");
    } else {
      const checkbox = page.getByRole("checkbox", {
        name: /charge my laptop through this accessory/i,
      });
      await setLaptopCharging(page, !(await checkbox.isChecked()));
    }
    return;
  }

  const control =
    label === "Laptop"
      ? page.getByLabel("Your laptop", { exact: true })
      : label === "Accessory"
        ? page.getByRole("combobox", {
            name: "Connect a dock, hub or charger",
          })
        : label === "External displays"
          ? page.getByRole("combobox", {
              name: /^External (displays|screens)/i,
            })
          : page.getByRole("combobox", {
              name: new RegExp(`^${label}`, "i"),
            });
  const selected = await control.inputValue();
  const other = await control
    .locator("option")
    .evaluateAll(
      (options: HTMLOptionElement[], current: string) =>
        options.find((option) => option.value !== current && !option.disabled)
          ?.value,
      selected,
    );
  expect(other).not.toBeUndefined();
  await control.selectOption(other ?? "");
}

test("shows a supported result with requirements, limits, and verified evidence", async ({
  page,
}) => {
  await page.goto("/");
  await chooseFixture(page);
  await openSetupFields(page);
  await setLaptopCharging(page, true);
  await page.getByRole("button", { name: /check my setup/i }).click();

  await expect(
    page.getByRole("heading", { name: /compatible/i }),
  ).toBeVisible();
  await expect(
    page.getByText("Physical connection", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("USB-C video", { exact: true })).toBeVisible();
  await expect(page.getByText("Charging", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("list", { name: "Known limitations" }),
  ).toHaveCount(0);
  await expect(page.getByText("SPECIFICATION SOURCES")).toBeVisible();
  await page
    .getByText("Synthetic E2E manufacturer specification", { exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: /Synthetic E2E fixture documents/ }),
  ).toHaveCount(6);
});

test("distinguishes documented incompatibility from missing display-mode data", async ({
  page,
}) => {
  await page.goto("/");
  await chooseFixture(page, "E2E No Video Laptop");
  await openSetupFields(page);
  await setLaptopCharging(page, false);
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(
    page.getByRole("heading", {
      name: /incompatible|doesn’t meet this setup/i,
    }),
  ).toBeVisible();
  await expect(page.getByText(/^(FAILED|NOT SUPPORTED)$/i)).toBeVisible();

  await chooseFixture(page, "E2E Unknown Mode Laptop");
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(
    page.getByRole("heading", {
      name: /insufficient data|not enough information/i,
    }),
  ).toBeVisible();
  await expect(page.getByText(/^(UNVERIFIED|NOT VERIFIED)$/i)).toBeVisible();

  const missingDataRegion = page.getByRole("region", {
    name: "Missing specifications breakdown",
  });
  await expect(missingDataRegion).toBeVisible();
  await expect(
    missingDataRegion.getByText("What manufacturer data is missing?"),
  ).toBeVisible();
  const unverifiedList = page.getByRole("list", {
    name: "Unverified requirements",
  });
  await expect(unverifiedList).toBeVisible();
  await expect(unverifiedList.locator("li")).not.toHaveCount(0);
});

test("clears a previous result when any device or setup input changes", async ({
  page,
}) => {
  await page.goto("/");
  await submitSupportedCheck(page);

  for (const label of [
    "Laptop",
    "Accessory",
    "External displays",
    "Resolution",
    "Refresh",
    "Laptop charging",
  ]) {
    await changeSelect(page, label);
    await expect(
      page.getByRole("button", { name: /share this result/i }),
    ).toHaveCount(0);
    if (label !== "Laptop charging") await submitSupportedCheck(page);
  }
});

test("copies a share URL and restores the setup in a fresh browser context", async ({
  page,
  browser,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async (text: string) => {
          Object.defineProperty(window, "__portpilotClipboard", {
            configurable: true,
            value: text,
          });
        },
      },
    });
  });
  await page.goto("/");
  await chooseFixture(page, "E2E Unknown Mode Laptop");
  await openSetupFields(page);
  await page
    .getByRole("combobox", { name: /^External (displays|screens)/i })
    .selectOption("1");
  await page.getByLabel("Resolution").selectOption("2560x1440");
  await page.getByLabel("Refresh").selectOption("30");
  await setLaptopCharging(page, false);
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(
    page.getByRole("heading", {
      name: /insufficient data|not enough information/i,
    }),
  ).toBeVisible();
  const sharedUrl = page.url();
  expect(sharedUrl).toContain("laptop=e2e-unknown-laptop");

  await page.getByRole("button", { name: /share this result/i }).click();
  await expect(page.locator(".share-message")).toHaveText("Link copied");
  await expect
    .poll(async () =>
      page.evaluate(
        () =>
          (window as Window & { __portpilotClipboard?: string })
            .__portpilotClipboard,
      ),
    )
    .toBe(sharedUrl);

  const freshContext = await browser.newContext();
  const sharedPage = await freshContext.newPage();
  await sharedPage.goto(sharedUrl);
  await openSetupFields(sharedPage);
  await expect(
    sharedPage.getByLabel("Your laptop", { exact: true }),
  ).toHaveValue("e2e-unknown-laptop");
  await expect(sharedPage.getByLabel("Resolution")).toHaveValue("2560x1440");
  await expect(sharedPage.getByLabel("Refresh")).toHaveValue("30");
  await expectLaptopCharging(sharedPage, false);
  await expect(
    sharedPage.getByRole("heading", {
      name: /insufficient data|not enough information/i,
    }),
  ).toBeVisible();
  await freshContext.close();
});

test("provides a clipboard fallback when browser clipboard access fails", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: () => Promise.reject(new Error("Clipboard unavailable")),
      },
    });
  });
  await page.goto("/");
  await submitSupportedCheck(page);
  await page.getByRole("button", { name: /share this result/i }).click();
  await expect(page.locator(".share-message")).toHaveText(
    "Copy the link from your address bar",
  );
});

test("submits a low-data report with deterministic result context", async ({
  page,
}) => {
  let submitted: Record<string, unknown> | undefined;
  await page.route(`${apiOrigin}/result-reports`, async (route) => {
    submitted = route.request().postDataJSON();
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ id: "report-test", status: "received" }),
    });
  });
  await page.goto("/");
  await submitSupportedCheck(page);
  await page.getByText("Think this result is wrong? Report it").click();
  await page
    .getByLabel("What seems wrong? (optional)")
    .fill("The display result seems incorrect.");
  await page.getByRole("button", { name: "Send report" }).click();
  await expect(page.locator(".result-report").getByRole("status")).toHaveText(
    "Thanks. Your report was sent to the PortPilot team.",
  );
  expect(submitted).toMatchObject({
    laptop_id: "e2e-good-laptop",
    accessory_id: "e2e-good-hub",
    verdict: "compatible",
    rule_engine_version: "0.6.0",
    note: "The display result seems incorrect.",
  });
  expect(submitted).not.toHaveProperty("user_agent");
  expect(submitted).not.toHaveProperty("serial_number");
  expect(submitted).not.toHaveProperty("reply_email");
});

test("keeps device selection and evidence readable at a narrow viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  await chooseFixture(page);
  await page.getByText("See verified details").first().click();
  await expect(page.getByLabel("Your laptop", { exact: true })).toBeVisible();
  await expect(page.getByText("Selected model code:").first()).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflow).toBe(false);
});

test("shows a catalogue error and recovers when the API returns", async ({
  page,
}) => {
  await page.route(`${apiOrigin}/devices`, (route) =>
    route.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
  );
  await page.goto("/");
  await expect(
    page.getByText(
      /device catalogue could not be loaded|couldn’t load the device list/i,
      {
        exact: true,
      },
    ),
  ).toBeVisible();
  await page.unroute(`${apiOrigin}/devices`);
  await page.reload();
  await expect(page.getByLabel("Your laptop", { exact: true })).toContainText(
    "E2E Supported Laptop",
  );
  await expect(
    page.getByText(
      /device catalogue could not be loaded|couldn’t load the device list/i,
      { exact: true },
    ),
  ).toHaveCount(0);
});

test("shows a check error without retaining a stale result, then recovers", async ({
  page,
}) => {
  await page.goto("/");
  await submitSupportedCheck(page);
  await page.route(`${apiOrigin}/checks`, (route) =>
    route.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
  );
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(
    page.getByText("The compatibility service could not complete this check.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /share this result/i }),
  ).toHaveCount(0);

  await page.unroute(`${apiOrigin}/checks`);
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(
    page.getByRole("heading", { name: /compatible/i }),
  ).toBeVisible();
});

test("renders live coverage and navigates back to the checker", async ({
  page,
}) => {
  await page.goto("/coverage");
  await expect(
    page.getByRole("heading", { name: "Know what we cover." }),
  ).toBeVisible();
  await expect(
    page.getByText("verified laptops", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("verified accessories", { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Back to checker" }).click();
  await expect(
    page.getByRole("heading", { name: /will your (gear|devices)/i }),
  ).toBeVisible();
});
