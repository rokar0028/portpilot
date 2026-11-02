import { expect, test } from "@playwright/test";

const apiOrigin = process.env.PORTPILOT_E2E_API_URL ?? "http://127.0.0.1:18000";

test("loads the verified catalogue in the production standalone frontend", async ({
  page,
}) => {
  const pageErrors: string[] = [];
  const failedApiRequests: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("requestfailed", (request) => {
    if (request.url().startsWith(apiOrigin))
      failedApiRequests.push(request.url());
  });

  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /will your gear/i }),
  ).toBeVisible();
  await expect(page.getByLabel("Laptop", { exact: true })).toContainText(
    "E2E Supported Laptop",
  );
  await expect(page.getByLabel("Accessory", { exact: true })).toContainText(
    "E2E Supported Hub",
  );
  await expect(page.getByLabel("Laptop", { exact: true })).not.toContainText(
    "E2E Unreviewed Laptop",
  );
  await expect(page.getByLabel("Accessory", { exact: true })).not.toContainText(
    "E2E Unreviewed Hub",
  );
  expect(pageErrors).toEqual([]);
  expect(failedApiRequests).toEqual([]);
});
