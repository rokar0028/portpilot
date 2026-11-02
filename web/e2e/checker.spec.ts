import { expect, test, type Page } from "@playwright/test";

const apiOrigin = process.env.PORTPILOT_E2E_API_URL ?? "http://127.0.0.1:18000";

async function chooseFixture(page: Page, laptop = "E2E Supported Laptop") {
  await page
    .getByLabel("Laptop", { exact: true })
    .selectOption({ label: laptop });
  await page
    .getByLabel("Accessory", { exact: true })
    .selectOption({ label: "E2E Supported Hub" });
}

async function submitSupportedCheck(page: Page) {
  await chooseFixture(page);
  await page.getByLabel("Laptop charging").selectOption("false");
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(page.getByRole("heading", { name: "compatible" })).toBeVisible();
}

async function changeSelect(page: Page, label: string) {
  const control = ["Laptop", "Accessory"].includes(label)
    ? page.getByLabel(label, { exact: true })
    : page.getByRole("combobox", { name: new RegExp(`^${label}`) });
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
  await page.getByLabel("Laptop charging").selectOption("true");
  await page.getByRole("button", { name: /check my setup/i }).click();

  await expect(page.getByRole("heading", { name: "compatible" })).toBeVisible();
  await expect(
    page.getByText("Physical connection", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("USB-C video", { exact: true })).toBeVisible();
  await expect(page.getByText("Charging", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("list", { name: "Known limitations" }),
  ).toHaveCount(0);
  await expect(page.getByText("SPECIFICATION SOURCES")).toBeVisible();
  await expect(
    page.getByRole("link", {
      name: /Synthetic E2E manufacturer specification/,
    }),
  ).toHaveCount(6);
});

test("distinguishes documented incompatibility from missing display-mode data", async ({
  page,
}) => {
  await page.goto("/");
  await chooseFixture(page, "E2E No Video Laptop");
  await page.getByLabel("Laptop charging").selectOption("false");
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(
    page.getByRole("heading", { name: "incompatible" }),
  ).toBeVisible();
  await expect(page.getByText("FAILED", { exact: true })).toBeVisible();

  await chooseFixture(page, "E2E Unknown Mode Laptop");
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(
    page.getByRole("heading", { name: "insufficient data" }),
  ).toBeVisible();
  await expect(page.getByText("UNVERIFIED", { exact: true })).toBeVisible();
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
  context,
  browser,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/");
  await chooseFixture(page, "E2E Unknown Mode Laptop");
  await page.getByLabel("External displays").selectOption("1");
  await page.getByLabel("Resolution").selectOption("2560x1440");
  await page.getByLabel("Refresh").selectOption("30");
  await page.getByLabel("Laptop charging").selectOption("false");
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(
    page.getByRole("heading", { name: "insufficient data" }),
  ).toBeVisible();
  const sharedUrl = page.url();
  expect(sharedUrl).toContain("laptop=e2e-unknown-laptop");

  await page.getByRole("button", { name: /share this result/i }).click();
  await expect(page.getByRole("status")).toHaveText("Link copied");
  await expect
    .poll(async () => page.evaluate(() => navigator.clipboard.readText()))
    .toBe(sharedUrl);

  const freshContext = await browser.newContext();
  const sharedPage = await freshContext.newPage();
  await sharedPage.goto(sharedUrl);
  await expect(sharedPage.getByLabel("Laptop", { exact: true })).toHaveValue(
    "e2e-unknown-laptop",
  );
  await expect(sharedPage.getByLabel("Resolution")).toHaveValue("2560x1440");
  await expect(sharedPage.getByLabel("Refresh")).toHaveValue("30");
  await expect(sharedPage.getByLabel("Laptop charging")).toHaveValue("false");
  await expect(
    sharedPage.getByRole("heading", { name: "insufficient data" }),
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
  await expect(page.getByRole("status")).toHaveText(
    "Copy the link from your address bar",
  );
});

test("shows a catalogue error and recovers when the API returns", async ({
  page,
}) => {
  await page.route(`${apiOrigin}/devices`, (route) =>
    route.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
  );
  await page.goto("/");
  await expect(
    page.getByText("The device catalogue could not be loaded.", {
      exact: true,
    }),
  ).toBeVisible();
  await page.unroute(`${apiOrigin}/devices`);
  await page.reload();
  await expect(page.getByLabel("Laptop", { exact: true })).toContainText(
    "E2E Supported Laptop",
  );
  await expect(
    page.getByText("The device catalogue could not be loaded.", {
      exact: true,
    }),
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
  await expect(page.getByRole("heading", { name: "compatible" })).toBeVisible();
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
    page.getByRole("heading", { name: /will your gear/i }),
  ).toBeVisible();
});
