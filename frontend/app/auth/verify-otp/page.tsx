'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle, AlertCircle, Loader, Lock } from 'lucide-react';
import axios from 'axios';
import Link from 'next/link';

// Force dynamic rendering to avoid static generation memory issues
export const dynamic = 'force-dynamic';

export default function VerifyOTPPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [status, setStatus] = useState<'loading' | 'entering' | 'verifying' | 'success' | 'error'>('entering');
    const [message, setMessage] = useState('Enter the OTP code sent to your email');
    const [otp, setOtp] = useState('');
    const [userId, setUserId] = useState<string | null>(null);
    const [resendCooldown, setResendCooldown] = useState(0);

    useEffect(() => {
        const userIdParam = searchParams.get('user_id');
        if (userIdParam) {
            setUserId(userIdParam);
        }
    }, [searchParams]);

    useEffect(() => {
        if (resendCooldown > 0) {
            const timer = setTimeout(() => {
                setResendCooldown(resendCooldown - 1);
            }, 1000);
            return () => clearTimeout(timer);
        }
    }, [resendCooldown]);

    const verifyOTP = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!otp || otp.length !== 6) {
            setStatus('error');
            setMessage('Please enter a valid 6-digit OTP code');
            return;
        }

        if (!userId) {
            setStatus('error');
            setMessage('User ID not found. Please sign up again.');
            return;
        }

        try {
            setStatus('verifying');
            setMessage('Verifying OTP code...');

            const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
            const response = await axios.post(
                `${backendUrl}/auth/verify-otp`,
                {
                    user_id: userId,
                    otp_code: otp
                }
            );

            setStatus('success');
            setMessage('✓ Email verified successfully! Redirecting to login...');
            
            setTimeout(() => {
                router.push('/auth/login');
            }, 2000);
        } catch (err: any) {
            setStatus('error');
            setMessage(
                err.response?.data?.detail || 'Invalid OTP code. Please try again.'
            );
            setOtp('');
        }
    };

    const resendOTP = async () => {
        if (!userId) {
            setMessage('User ID not found. Please sign up again.');
            return;
        }

        try {
            setMessage('Sending new OTP code...');
            const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
            
            await axios.post(
                `${backendUrl}/auth/resend-otp`,
                { user_id: userId }
            );

            setMessage('✓ OTP code sent to your email');
            setResendCooldown(60);
        } catch (err: any) {
            setMessage(
                err.response?.data?.detail || 'Failed to resend OTP. Please try again.'
            );
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 flex flex-col items-center justify-center relative overflow-hidden p-4">
            {/* Animated Background */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-[-10%] left-[-5%] w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-3xl" style={{ animationDelay: '1s' }}></div>
            </div>

            <div className="z-10 w-full max-w-md">
                {/* Success State */}
                {status === 'success' && (
                    <div className="bg-slate-900/50 backdrop-blur-lg border border-emerald-500/30 rounded-xl p-8 shadow-xl">
                        <div className="flex justify-center mb-6">
                            <CheckCircle className="w-16 h-16 text-emerald-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-center text-emerald-400 mb-2">Email Verified!</h2>
                        <p className="text-center text-slate-300">{message}</p>
                    </div>
                )}

                {/* Error State */}
                {status === 'error' && (
                    <div className="bg-slate-900/50 backdrop-blur-lg border border-red-500/30 rounded-xl p-8 shadow-xl">
                        <div className="flex justify-center mb-6">
                            <AlertCircle className="w-16 h-16 text-red-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-center text-red-400 mb-2">Verification Failed</h2>
                        <p className="text-center text-slate-300 mb-6">{message}</p>
                        
                        <form onSubmit={verifyOTP} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    OTP Code (6 digits)
                                </label>
                                <input
                                    type="text"
                                    maxLength={6}
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, ''))}
                                    placeholder="000000"
                                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-center text-2xl tracking-widest font-mono text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={otp.length !== 6}
                                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                            >
                                Verify OTP
                            </button>
                        </form>

                        <div className="mt-4 text-center">
                            <button
                                onClick={resendOTP}
                                disabled={resendCooldown > 0}
                                className="text-blue-400 hover:text-blue-300 disabled:text-slate-600 text-sm font-medium"
                            >
                                {resendCooldown > 0 ? `Resend OTP in ${resendCooldown}s` : 'Resend OTP'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Entering State */}
                {(status === 'entering' || status === 'loading') && (
                    <div className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-xl p-8 shadow-xl">
                        <div className="flex justify-center mb-6">
                            <Lock className="w-16 h-16 text-blue-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-center text-white mb-2">Verify Your Email</h2>
                        <p className="text-center text-slate-400 mb-6">{message}</p>
                        
                        <form onSubmit={verifyOTP} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    OTP Code (6 digits)
                                </label>
                                <input
                                    type="text"
                                    maxLength={6}
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, ''))}
                                    placeholder="000000"
                                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-center text-2xl tracking-widest font-mono text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors"
                                    autoFocus
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={otp.length !== 6}
                                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                            >
                                {status === 'verifying' ? (
                                    <>
                                        <Loader className="w-5 h-5 animate-spin" />
                                        Verifying...
                                    </>
                                ) : (
                                    'Verify OTP'
                                )}
                            </button>
                        </form>

                        <div className="mt-6 text-center">
                            <p className="text-slate-400 text-sm mb-4">Didn't receive the code?</p>
                            <button
                                onClick={resendOTP}
                                disabled={resendCooldown > 0}
                                className="text-blue-400 hover:text-blue-300 disabled:text-slate-600 font-medium"
                            >
                                {resendCooldown > 0 ? `Resend OTP in ${resendCooldown}s` : 'Resend OTP'}
                            </button>
                        </div>

                        <div className="mt-6 text-center">
                            <Link href="/auth/login" className="text-slate-400 hover:text-slate-300 text-sm">
                                Back to Login
                            </Link>
                        </div>
                    </div>
                )}

                {/* Verifying State */}
                {status === 'verifying' && (
                    <div className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-xl p-8 shadow-xl">
                        <div className="flex justify-center mb-6">
                            <Loader className="w-16 h-16 text-blue-500 animate-spin" />
                        </div>
                        <h2 className="text-2xl font-bold text-center text-white mb-2">Verifying OTP</h2>
                        <p className="text-center text-slate-400">{message}</p>
                    </div>
                )}
            </div>
        </div>
    );
}
