import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Memory optimization for Vercel builds
  experimental: {
    // Reduce memory usage during build
    workerThreads: false,
    cpus: 1,
    optimizePackageImports: ["@radix-ui/react-icons", "lucide-react"],
  },

  // Disable source maps in production to save memory
  productionBrowserSourceMaps: false,

  // Enable incremental static regeneration to reduce memory
  onDemandEntries: {
    maxInactiveAge: 15 * 60 * 1000,
    pagesBufferLength: 2,
  },
};

export default nextConfig;
