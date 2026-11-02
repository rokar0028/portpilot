import { defineConfig, devices } from "@playwright/test";

const apiUrl = process.env.PORTPILOT_E2E_API_URL ?? "http://127.0.0.1:18000";
const webUrl = process.env.PORTPILOT_E2E_WEB_URL ?? "http://127.0.0.1:13000";
const apiPort = new URL(apiUrl).port;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]]
    : "list",
  outputDir: "test-results",
  use: {
    baseURL: webUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: `python -m uvicorn app.main:app --host 127.0.0.1 --port ${apiPort}`,
      cwd: "../api",
      url: `${apiUrl}/ready`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: "node .next/standalone/server.js",
      url: webUrl,
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        ...process.env,
        HOSTNAME: "127.0.0.1",
        PORT: new URL(webUrl).port,
      },
    },
  ],
});
