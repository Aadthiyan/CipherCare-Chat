import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Use streaming for dynamic rendering to avoid static generation memory issues
  output: 'standalone',

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
};

export default nextConfig;
