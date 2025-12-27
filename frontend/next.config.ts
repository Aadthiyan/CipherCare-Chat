import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Skip static generation during build to avoid memory issues
  // Pages will be generated on-demand (Incremental Static Regeneration)
  typescript: {
    ignoreBuildErrors: false,
  },

  // Memory optimization for Vercel builds
  experimental: {
    // Reduce memory usage during build
    workerThreads: false,
    cpus: 1,
    optimizePackageImports: ["@radix-ui/react-icons", "lucide-react"],
  },

  // Disable source maps in production to save memory
  productionBrowserSourceMaps: false,

  // Reduce build cache to free up memory
  onDemandEntries: {
    maxInactiveAge: 1 * 60 * 1000, // 1 minute
    pagesBufferLength: 1,
  },

  // Skip full static optimization during build
  staticPageGenerationTimeout: undefined,
};

export default nextConfig;
