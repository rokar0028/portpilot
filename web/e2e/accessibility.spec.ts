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
  await expect(page.getByLabel("Laptop", { exact: true })).toBeEnabled();

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
  await expect(page.getByLabel("Laptop", { exact: true })).toBeEnabled();

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
