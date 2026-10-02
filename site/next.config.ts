import type { NextConfig } from "next";

// Static export. Default: GitHub Pages at https://kuyaloy.github.io/convert-wordpress-skill/
// Another host: set SITE_URL (the full address) and SITE_BASE_PATH ("" for a subdomain, "/folder" for a subfolder).
const basePath = process.env.SITE_BASE_PATH ?? "/convert-wordpress-skill";
const siteUrl = process.env.SITE_URL ?? "https://kuyaloy.github.io/convert-wordpress-skill/";

const nextConfig: NextConfig = {
  output: "export",
  basePath,
  trailingSlash: true,
  images: { unoptimized: true },
  env: { NEXT_PUBLIC_BASE_PATH: basePath, NEXT_PUBLIC_SITE_URL: siteUrl },
};

export default nextConfig;
