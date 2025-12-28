'use client';

import { Suspense } from 'react';
import VerifyOTPContent from './VerifyOTPContent';
import { Loader } from 'lucide-react';

// Force dynamic rendering to avoid static generation memory issues
export const dynamic = 'force-dynamic';

export default function VerifyOTPPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center relative overflow-hidden p-4">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
          <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-3xl"></div>
        </div>
        <div className="z-10 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Verify Your Account</h1>
            <p className="text-slate-400">Loading...</p>
          </div>
          <div className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-xl p-8 shadow-xl">
            <div className="flex justify-center mb-6">
              <Loader className="w-12 h-12 text-blue-500 animate-spin" />
            </div>
            <p className="text-center text-lg text-slate-300">Loading...</p>
          </div>
        </div>
      </div>
    }>
      <VerifyOTPContent />
    </Suspense>
  );
}
