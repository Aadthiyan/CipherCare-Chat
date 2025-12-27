'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Heart, Lock, User, AlertCircle, Loader } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState('jsmith');
  const [password, setPassword] = useState('Aadhithiyan@99');
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    console.log('🔐 Attempting login...');

    try {
      // Use auth context login method
      console.log('📡 Using auth context to login...');
      await login(username, password);

      console.log('✅ Login successful via auth context');

      // Remember me: store credentials (insecure in production!)
      if (rememberMe) {
        localStorage.setItem('remember_username', username);
      } else {
        localStorage.removeItem('remember_username');
      }

      // Wait a moment for auth state to update
      console.log('⏳ Waiting for auth state to update...');
      await new Promise(resolve => setTimeout(resolve, 500));

      // Redirect to dashboard
      console.log('🚀 Redirecting to dashboard...');
      router.push('/dashboard');
    } catch (err: any) {
      console.error('❌ Login error:', err);
      setError(err.message || 'Login failed. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e1a] flex flex-col relative overflow-hidden medical-grid">
      {/* Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-3xl float-animation"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-3xl float-animation" style={{ animationDelay: '1s' }}></div>
      </div>

      {/* Navbar */}
      <nav className="z-10 px-8 py-6 flex justify-between items-center border-b border-white/5 backdrop-blur-sm">
        <Link href="/" className="flex items-center gap-3">
          <div className="relative">
            <Heart className="w-8 h-8 text-blue-400 heartbeat" fill="currentColor" />
            <div className="absolute inset-0 w-8 h-8 text-blue-400 opacity-30 blur-sm">
              <Heart className="w-8 h-8" fill="currentColor" />
            </div>
          </div>
          <span className="text-2xl font-bold text-gradient-medical">
            CiperCare
          </span>
        </Link>
      </nav>

      {/* Login Form */}
      <main className="flex-1 flex items-center justify-center z-10 px-4">
        <div className="w-full max-w-md">
          <div className="glass-card border border-blue-500/10 rounded-2xl p-8 medical-shadow-lg">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <div className="p-3 rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-400/30">
                  <Lock className="w-6 h-6 text-blue-400" />
                </div>
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">Welcome Back</h1>
              <p className="text-slate-400">Sign in to your clinician account</p>
            </div>

            {/* Error Alert */}
            {error && (
              <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 flex gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-red-300 text-sm">{error}</p>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleLogin} className="space-y-5">
              {/* Username */}
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
                  Username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="attending or resident"
                    className="w-full glass-card border border-blue-500/20 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400 transition"
                    disabled={loading}
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full glass-card border border-blue-500/20 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400 transition"
                    disabled={loading}
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">Demo: password123</p>
              </div>

              {/* Remember Me */}
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-blue-400/30 bg-slate-800 accent-blue-500"
                  disabled={loading}
                />
                <span className="text-sm text-slate-400">Remember me</span>
              </label>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full mt-8 px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-400 hover:to-cyan-400 disabled:from-slate-700 disabled:to-slate-700 text-white font-bold rounded-lg transition-all shadow-xl shadow-blue-500/30 flex items-center justify-center gap-2 disabled:shadow-none"
              >
                {loading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    <Lock className="w-5 h-5" />
                    Sign In
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-slate-900/50 text-slate-500">Don't have an account?</span>
              </div>
            </div>

            {/* Signup Link */}
            <Link
              href="/auth/signup"
              className="block w-full text-center px-6 py-3 glass-card border border-blue-500/30 hover:border-blue-400 text-blue-300 hover:text-blue-200 font-semibold rounded-lg transition-all"
            >
              Create Account
            </Link>

            {/* Help Links */}
            <div className="mt-6 space-y-2 text-center text-sm">
              <Link href="/auth/forgot-password" className="text-slate-400 hover:text-slate-300 block transition">
                Forgot password?
              </Link>
              <Link href="/" className="text-slate-500 hover:text-slate-400 block transition">
                Back to home
              </Link>
            </div>
          </div>

          {/* Info Card */}
          <div className="mt-6 p-4 glass-card border border-blue-500/10 rounded-lg">
            <p className="text-xs text-slate-400 text-center">
              <strong className="text-blue-300">Demo Credentials:</strong><br />
              Attending: attending / password123<br />
              Resident: resident / password123
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
