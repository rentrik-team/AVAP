import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle (.next/standalone) so the Docker
  // runtime image ships only the compiled server + static assets, not the
  // full node_modules tree. Has no effect on `npm run dev`.
  output: "standalone",
};

export default nextConfig;
