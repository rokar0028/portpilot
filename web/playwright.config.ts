import fs from "node:fs";
import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const apiUrl = process.env.PORTPILOT_E2E_API_URL ?? "http://127.0.0.1:18000";
const webUrl = process.env.PORTPILOT_E2E_WEB_URL ?? "http://127.0.0.1:13000";
const apiPort = new URL(apiUrl).port;
const venvRelative =
  process.platform === "win32"
    ? "../api/.venv/Scripts/python.exe"
    : "../api/.venv/bin/python";
const venvPython = path.resolve(venvRelative);
const pythonCmd = fs.existsSync(venvPython) ? `"${venvPython}"` : "python";
const projects = [
  { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  { name: "firefox", use: { ...devices["Desktop Firefox"] } },
  { name: "webkit", use: { ...devices["Desktop Safari"] } },
];
const requestedBrowser = process.env.PORTPILOT_E2E_BROWSER;

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
  projects:
    process.env.PORTPILOT_E2E_CROSS_BROWSER === "1"
      ? projects.filter(
          (project) => !requestedBrowser || project.name === requestedBrowser,
        )
      : projects.slice(0, 1),
  webServer: [
    {
      command: `${pythonCmd} -m uvicorn app.main:app --host 127.0.0.1 --port ${apiPort}`,
      cwd: "../api",
      url: `${apiUrl}/ready`,
      reuseExistingServer: true,
      timeout: 60_000,
      env: {
        ...process.env,
        FRONTEND_ORIGIN: webUrl,
      },
    },
    {
      command: "node node_modules/next/dist/bin/next start",
      url: webUrl,
      reuseExistingServer: true,
      timeout: 60_000,
      env: {
        ...process.env,
        PORTPILOT_E2E_DIST_DIR: ".next-e2e",
        HOSTNAME: "127.0.0.1",
        PORT: new URL(webUrl).port,
      },
    },
  ],
});
