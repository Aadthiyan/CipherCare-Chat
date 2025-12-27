import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Memory optimization for Vercel builds
  experimental: {
    // Reduce memory usage during build
    workerThreads: false,
    cpus: 1,
  },

  // Disable source maps in production to save memory
  productionBrowserSourceMaps: false,
};

export default nextConfig;
