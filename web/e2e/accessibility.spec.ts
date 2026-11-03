import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

function violationTargets(
  violations: Awaited<ReturnType<AxeBuilder["analyze"]>>["violations"],
) {
  return violations.map(
    (violation) =>
      `${violation.impact}: ${violation.id} — ${violation.nodes
        .map((node) => node.target.join(" "))
        .join(", ")}`,
  );
}

test("checker has no WCAG 2.1 A/AA automated accessibility violations", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByLabel("Your laptop", { exact: true })).toBeEnabled();

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();

  expect(violationTargets(results.violations)).toEqual([]);
});

test("coverage page has no WCAG 2.1 A/AA automated accessibility violations", async ({
  page,
}) => {
  await page.goto("/coverage");
  await expect(
    page.getByText("verified laptops", { exact: true }),
  ).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();

  expect(violationTargets(results.violations)).toEqual([]);
});

test("checker controls are keyboard reachable and usable on a narrow viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/");
  await expect(page.getByLabel("Your laptop", { exact: true })).toBeEnabled();

  let laptopFocused = false;
  for (let tab = 0; tab < 12 && !laptopFocused; tab += 1) {
    await page.keyboard.press("Tab");
    laptopFocused = await page.evaluate(
      () => document.activeElement?.id === "laptop",
    );
  }
  expect(laptopFocused).toBe(true);

  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth,
  }));
  expect(dimensions.content).toBeLessThanOrEqual(dimensions.viewport);
});

test("announces parsed setup review, results, and service errors concisely", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByLabel("Your laptop", { exact: true })).toBeEnabled();

  await page.getByText("Adjust screen or charging needs").click();
  await page
    .getByLabel("Describe your setup (optional)")
    .fill("one 4K display at 60 Hz");
  await page.route("**/setup-requests/parse", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        setup: {
          external_displays: 1,
          resolution: "3840x2160",
          refresh_rate_hz: 60,
          laptop_charging: null,
        },
        needs_clarification: false,
        clarification_questions: [],
        unsupported_requests: [],
        notice:
          "Review extracted fields before running the compatibility check.",
      }),
    }),
  );
  await page.getByRole("button", { name: "Interpret setup" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Setup interpreted. Review the extracted requirements and confirm them before checking.",
  );
  await expect(
    page.getByRole("checkbox", { name: /I reviewed these requirements/ }),
  ).toBeVisible();

  const parsedResults = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(violationTargets(parsedResults.violations)).toEqual([]);

  await page
    .getByRole("checkbox", { name: /I reviewed these requirements/ })
    .check();
  await page
    .getByLabel("Your laptop", { exact: true })
    .selectOption({ index: 1 });
  await page.locator("#accessory").selectOption({ index: 1 });
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(page.getByRole("status")).toContainText("Check complete.");

  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(violationTargets(result.violations)).toEqual([]);

  await page.route("**/checks", (route) =>
    route.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
  );
  await page.getByRole("button", { name: /check my setup/i }).click();
  await expect(page.locator(".form-error[role=alert]")).toContainText(
    "The compatibility service could not complete this check.",
  );
  const error = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(violationTargets(error.violations)).toEqual([]);
});
