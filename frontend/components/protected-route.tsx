/**
 * Protected Route - Redirects unauthenticated users to login
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      console.log('🔐 ProtectedRoute: Not authenticated, redirecting to login...');
      // Use router.push with a fallback to window.location
      router.push('/auth/login');
      
      // Fallback: if redirect doesn't work after 2 seconds, use window.location
      const timeout = setTimeout(() => {
        if (typeof window !== 'undefined') {
          console.log('🔐 ProtectedRoute: Using fallback redirect...');
          window.location.href = '/auth/login';
        }
      }, 2000);
      
      return () => clearTimeout(timeout);
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0e1a]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading secure session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0e1a]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
