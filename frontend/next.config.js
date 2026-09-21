/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Hide the dev-mode route/build indicator overlay from every screen, including patient-facing ones.
  devIndicators: false,
  // Pin the workspace root so Turbopack doesn't get confused by the root-level package-lock.json.
  turbopack: {
    root: __dirname,
  },
};

module.exports = nextConfig;
