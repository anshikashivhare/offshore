/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // MapLibre ships as ESM-only; Next handles it, but we keep transpilePackages
  // explicit so future custom layers don't need additional config.
  transpilePackages: ["maplibre-gl"],
};

export default nextConfig;