/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Disable strict typed routes for now to avoid breaking builds
  // while routes are still evolving quickly.
  typedRoutes: false
};

export default nextConfig;
