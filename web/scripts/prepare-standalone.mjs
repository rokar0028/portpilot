import { cp, mkdir } from "node:fs/promises";

const standalone = new URL("../.next/standalone/", import.meta.url);
const staticFiles = new URL("../.next/static/", import.meta.url);
const standaloneStatic = new URL(
  "../.next/standalone/.next/static/",
  import.meta.url,
);
const publicFiles = new URL("../public/", import.meta.url);
const standalonePublic = new URL(
  "../.next/standalone/public/",
  import.meta.url,
);

await mkdir(standaloneStatic, { recursive: true });
await cp(staticFiles, standaloneStatic, { recursive: true });
try {
  await cp(publicFiles, standalonePublic, { recursive: true });
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}

console.log(`Prepared standalone frontend at ${standalone.pathname}`);
