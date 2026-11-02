import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  ...(process.env.PORTPILOT_E2E_DIST_DIR
    ? { distDir: process.env.PORTPILOT_E2E_DIST_DIR }
    : {}),
};

export default nextConfig;
