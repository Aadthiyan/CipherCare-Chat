'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle, AlertCircle, Loader, Lock } from 'lucide-react';
import axios from 'axios';

export default function VerifyOTPPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'input' | 'loading' | 'success' | 'error'>('input');
  const [message, setMessage] = useState('');
  const [otpInput, setOtpInput] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [timeLeft, setTimeLeft] = useState(900); // 15 minutes
  
  const userId = searchParams.get('user_id');
  const prefilledOtp = searchParams.get('otp');

  useEffect(() => {
    // Countdown timer
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          setStatus('error');
          setMessage('OTP has expired. Please sign up again.');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!otpInput.trim()) {
      setMessage('Please enter the OTP code');
      return;
    }

    if (!userId) {
      setMessage('User ID missing. Please sign up again.');
      return;
    }

    setStatus('loading');
    setMessage('Verifying OTP...');

    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/auth/verify-otp',
        {
          user_id: userId,
          otp_code: otpInput.trim()
        }
      );

      setStatus('success');
      setMessage('Account verified successfully! Redirecting to login...');
      
      setTimeout(() => {
        router.push('/auth/login');
      }, 2000);
    } catch (error: any) {
      setAttempts(prev => prev + 1);
      
      if (attempts >= 2) {
        setStatus('error');
        setMessage('Too many failed attempts. Please sign up again.');
      } else {
        setStatus('input');
        setMessage(
          error.response?.data?.detail || `Invalid OTP. ${3 - attempts - 1} attempts remaining.`
        );
        setOtpInput('');
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center relative overflow-hidden p-4">
      {/* Gradient backgrounds */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Content */}
      <div className="z-10 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Verify Your Account</h1>
          <p className="text-slate-400">Enter the OTP code to complete registration</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-xl p-8 shadow-xl">
          {/* Status Icon */}
          <div className="flex justify-center mb-6">
            {status === 'loading' && (
              <Loader className="w-12 h-12 text-blue-500 animate-spin" />
            )}
            {status === 'success' && (
              <CheckCircle className="w-12 h-12 text-emerald-500" />
            )}
            {status === 'error' && (
              <AlertCircle className="w-12 h-12 text-red-500" />
            )}
            {status === 'input' && (
              <Lock className="w-12 h-12 text-blue-500" />
            )}
          </div>

          {/* Timer */}
          {status !== 'error' && status !== 'success' && (
            <div className="text-center mb-6">
              <p className="text-sm text-slate-400 mb-2">Time remaining:</p>
              <p className="text-2xl font-mono font-bold text-emerald-400">
                {formatTime(timeLeft)}
              </p>
            </div>
          )}

          {/* Message */}
          <p className={`text-center text-base mb-6 ${
            status === 'success' ? 'text-emerald-400' :
            status === 'error' ? 'text-red-400' :
            status === 'loading' ? 'text-blue-300' :
            'text-slate-300'
          }`}>
            {message}
          </p>

          {/* Show OTP for testing */}
          {prefilledOtp && (
            <div className="mb-6 bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
              <p className="text-sm text-amber-300 font-mono text-center">
                <span className="block text-xs uppercase tracking-wider opacity-75 mb-2">Test OTP Code:</span>
                <span className="text-2xl font-bold">{prefilledOtp}</span>
              </p>
            </div>
          )}

          {/* OTP Input Form */}
          {status === 'input' && (
            <form onSubmit={handleVerify} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  OTP Code (6 digits)
                </label>
                <input
                  type="text"
                  value={otpInput}
                  onChange={(e) => setOtpInput(e.target.value.replace(/[^0-9]/g, '').slice(0, 6))}
                  placeholder="000000"
                  maxLength={6}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-center text-2xl font-mono text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  autoFocus
                />
              </div>

              <button
                type="submit"
                className="w-full px-4 py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-bold rounded-lg transition duration-200"
              >
                Verify OTP
              </button>
            </form>
          )}

          {/* Info Box */}
          {prefilledOtp && status === 'input' && (
            <div className="mt-6 bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
              <p className="text-sm text-blue-300 font-mono">
                OTP Code: <span className="font-bold">{prefilledOtp}</span>
              </p>
            </div>
          )}

          {/* Error Recovery */}
          {status === 'error' && (
            <div className="space-y-4">
              <a
                href="/auth/signup"
                className="block w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition duration-200 text-center"
              >
                Back to Sign Up
              </a>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-slate-400 text-sm">
            Didn't get a code?{' '}
            <a href="/auth/signup" className="text-blue-400 hover:text-blue-300 font-semibold">
              Sign up again
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
