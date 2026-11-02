import { cp, mkdir } from "node:fs/promises";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = resolve(
  projectRoot,
  process.env.PORTPILOT_E2E_DIST_DIR ?? ".next",
);
const standalone = resolve(outputDir, "standalone");
const staticFiles = resolve(outputDir, "static");
const standaloneStatic = resolve(standalone, basename(outputDir), "static");
const publicFiles = resolve(projectRoot, "public");
const standalonePublic = resolve(standalone, "public");

await mkdir(standaloneStatic, { recursive: true });
await cp(staticFiles, standaloneStatic, { recursive: true });
try {
  await cp(publicFiles, standalonePublic, { recursive: true });
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}

console.log(`Prepared standalone frontend at ${standalone}`);
