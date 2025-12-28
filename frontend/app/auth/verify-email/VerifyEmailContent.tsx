'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle, AlertCircle, Loader, Mail } from 'lucide-react';
import axios from 'axios';

export default function VerifyEmailContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [message, setMessage] = useState('Verifying your email...');
    const token = searchParams.get('token');
    const [manualToken, setManualToken] = useState('');
    const [showManualInput, setShowManualInput] = useState(false);

    useEffect(() => {
        if (token) {
            verifyEmail(token);
        }
    }, [token]);

    const verifyEmail = async (verificationToken: string) => {
        try {
            setStatus('loading');
            setMessage('Verifying your email...');

            const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
            const response = await axios.post(
                `${backendUrl}/auth/verify-email`,
                { token: verificationToken },
                {
                    params: { token: verificationToken }
                }
            );

            setStatus('success');
            setMessage('Email verified successfully! Redirecting to login...');

            setTimeout(() => {
                router.push('/auth/login');
            }, 2000);
        } catch (error: any) {
            setStatus('error');
            setMessage(
                error.response?.data?.detail || 'Failed to verify email. The link may have expired.'
            );
            setShowManualInput(true);
        }
    };

    const handleManualVerify = async () => {
        if (!manualToken.trim()) {
            setMessage('Please enter a verification code');
            return;
        }
        await verifyEmail(manualToken);
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
                    <h1 className="text-3xl font-bold text-white mb-2">Verify Your Email</h1>
                    <p className="text-slate-400">Complete your account setup</p>
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
                            <AlertCircle className="w-12 h-12 text-amber-500" />
                        )}
                    </div>

                    {/* Message */}
                    <p className={`text-center text-lg mb-6 ${status === 'success' ? 'text-emerald-400' :
                            status === 'error' ? 'text-amber-400' :
                                'text-slate-300'
                        }`}>
                        {message}
                    </p>

                    {/* Manual Token Input */}
                    {showManualInput && (
                        <div className="space-y-4">
                            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                                <p className="text-sm text-slate-400 mb-3">
                                    Didn't get the automatic verification? Paste your verification code:
                                </p>
                                <input
                                    type="text"
                                    value={manualToken}
                                    onChange={(e) => setManualToken(e.target.value)}
                                    placeholder="Paste your verification code"
                                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                                />
                            </div>

                            <button
                                onClick={handleManualVerify}
                                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition duration-200"
                            >
                                Verify Code
                            </button>
                        </div>
                    )}

                    {/* Info Box */}
                    <div className="mt-6 bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                        <div className="flex gap-3">
                            <Mail className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-sm text-blue-300 font-semibold">Check your email</p>
                                <p className="text-xs text-blue-200">
                                    We've sent a verification link to your email address. Click the link to verify your account.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Resend Link */}
                    {status === 'error' && !showManualInput && (
                        <div className="mt-6 text-center">
                            <p className="text-sm text-slate-400 mb-3">
                                Didn't receive the email?
                            </p>
                            <button
                                onClick={() => router.push('/auth/resend-verification')}
                                className="text-blue-400 hover:text-blue-300 font-semibold text-sm"
                            >
                                Request a new verification link
                            </button>
                        </div>
                    )}
                </div>

                {/* Footer Links */}
                <div className="text-center mt-6">
                    <p className="text-slate-400 text-sm">
                        Already verified?{' '}
                        <a href="/auth/login" className="text-blue-400 hover:text-blue-300 font-semibold">
                            Go to login
                        </a>
                    </p>
                </div>
            </div>
        </div>
    );
}
