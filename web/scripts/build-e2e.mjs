import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const env = {
  ...process.env,
  NEXT_PUBLIC_API_URL:
    process.env.PORTPILOT_E2E_API_URL ?? "http://127.0.0.1:18000",
  PORTPILOT_E2E_DIST_DIR: ".next-e2e",
};
const nextCli = resolve(projectRoot, "node_modules/next/dist/bin/next");
const build = spawnSync(process.execPath, [nextCli, "build"], {
  cwd: projectRoot,
  env,
  stdio: "inherit",
});

if (build.status !== 0) process.exit(build.status ?? 1);

const prepare = spawnSync(
  process.execPath,
  ["scripts/prepare-standalone.mjs"],
  {
    cwd: projectRoot,
    env,
    stdio: "inherit",
  },
);
process.exit(prepare.status ?? 1);
