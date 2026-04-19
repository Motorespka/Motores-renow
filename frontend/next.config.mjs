import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "*.supabase.co", pathname: "/storage/v1/object/public/**" },
      { protocol: "https", hostname: "lh3.googleusercontent.com", pathname: "/**" },
    ],
  },
  // Disable strict typed routes for now to avoid breaking builds
  // while routes are still evolving quickly.
  typedRoutes: false,
  webpack: (config) => {
    config.resolve.alias["@repo/releases.json"] = path.join(__dirname, "..", "data", "releases.json");
    return config;
  },
};

export default nextConfig;
