import { expect, test, type Page } from "@playwright/test";

const apiOrigin = process.env.PORTPILOT_E2E_API_URL ?? "http://127.0.0.1:18000";
const setupFieldsOpened = new WeakSet<Page>();

async function prepareCheck(page: Page) {
  await page.goto("/");
  await page
    .getByLabel("Your laptop", { exact: true })
    .selectOption("e2e-good-laptop");
  await page
    .getByRole("combobox", { name: /^Accessory/ })
    .selectOption("e2e-good-hub");
  if (!setupFieldsOpened.has(page)) {
    const setupDisclosure = page.getByText("Change setup (optional)", {
      exact: true,
    });
    if (await setupDisclosure.count()) await setupDisclosure.click();
    setupFieldsOpened.add(page);
  }
  const chargingSelect = page.getByRole("combobox", {
    name: /^(Laptop charging|Charge laptop)/i,
  });
  if (await chargingSelect.count()) {
    await chargingSelect.selectOption("false");
  } else {
    await page
      .getByRole("checkbox", {
        name: /charge my laptop through this accessory/i,
      })
      .uncheck();
  }
}

test("discards an older response after a newer setup has completed", async ({
  page,
}) => {
  await prepareCheck(page);

  let releaseResponse = () => {};
  let requestIntercepted = () => {};
  const releaseGate = new Promise<void>((resolve) => {
    releaseResponse = resolve;
  });
  const intercepted = new Promise<void>((resolve) => {
    requestIntercepted = resolve;
  });
  await page.route(`${apiOrigin}/checks`, async (route) => {
    const laptopId = route.request().postDataJSON().laptop_id;
    if (laptopId === "e2e-good-laptop") {
      requestIntercepted();
      await releaseGate;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        verdict: laptopId === "e2e-good-laptop" ? "compatible" : "incompatible",
        summary: `Synthetic result for ${laptopId}.`,
        limits: [],
        requirements: [],
        evidence: [],
        rule_engine_version: "e2e",
      }),
    });
  });

  const checkButton = page.getByRole("button", {
    name: /check my setup|checking specifications/i,
  });
  const firstResponseReceived = page.waitForResponse(
    (response) =>
      response.url() === `${apiOrigin}/checks` &&
      response.request().postDataJSON().laptop_id === "e2e-good-laptop",
  );
  await checkButton.click();
  await intercepted;
  await expect(checkButton).toBeDisabled();
  await expect(checkButton).toHaveText(/checking specifications/i);

  await page.getByLabel("Your laptop", { exact: true }).selectOption({
    value: "e2e-bad-laptop",
  });
  const secondResponseReceived = page.waitForResponse(
    (response) =>
      response.url() === `${apiOrigin}/checks` &&
      response.request().postDataJSON().laptop_id === "e2e-bad-laptop",
  );
  await checkButton.click();
  await secondResponseReceived;
  await expect(
    page.getByRole("heading", {
      name: /incompatible|doesn’t meet this setup/i,
    }),
  ).toBeVisible();

  releaseResponse();
  await firstResponseReceived;
  await expect(checkButton).toBeEnabled();

  await expect(
    page.getByRole("heading", {
      name: /incompatible|doesn’t meet this setup/i,
    }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: /compatible/i })).toHaveCount(
    0,
  );
});
