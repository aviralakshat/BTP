import type { NextConfig } from "next"

const MODEL_API = process.env.MODEL_API_URL ?? "http://127.0.0.1:8000"

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    root: process.cwd(),
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [{ source: "/api/model/:path*", destination: `${MODEL_API}/api/:path*` }]
  },
}

export default nextConfig
