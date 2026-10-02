import type { NextConfig } from "next";

// Static export for GitHub Pages: https://kuyaloy.github.io/convert-wordpress-skill/
const basePath = process.env.SITE_BASE_PATH ?? "/convert-wordpress-skill";

const nextConfig: NextConfig = {
  output: "export",
  basePath,
  trailingSlash: true,
  images: { unoptimized: true },
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
};

export default nextConfig;
