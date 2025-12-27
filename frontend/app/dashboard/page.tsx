'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { Send, User, Bot, FileText, Search, AlertTriangle, CheckCircle, Activity } from 'lucide-react';
import { PatientSelector } from '@/components/patient-selector';
import { useAuth } from '@/lib/auth-context';

interface Source {
    type: string;
    date: string;
    snippet: string;
    similarity: number;
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
    sources?: Source[];
    confidence?: number;
}

export default function DashboardPage() {
    const router = useRouter();
    const { user, isAuthenticated, isLoading: authLoading } = useAuth();
    const [patientId, setPatientId] = useState('P123');
    const [patientName, setPatientName] = useState('John Doe'); // Add name state
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: 'Hello Dr. Smith. I have securely loaded the encryption keys. Which patient data would you like to query?' }
    ]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        // Add User Message
        const userMsg: Message = { role: 'user', content: query };
        setMessages(prev => [...prev, userMsg]);
        setQuery('');
        setLoading(true);

        try {
            // Get token from localStorage
            const token = localStorage.getItem('access_token');

            if (!token) {
                throw new Error('Authentication token not found. Please login again.');
            }

            // Call Next.js Proxy -> Backend with auth token
            const res = await axios.post('/api/query', {
                patient_id: patientId,
                question: userMsg.content,
                retrieve_k: 3,
                temperature: 0.1
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = res.data;

            const botMsg: Message = {
                role: 'assistant',
                content: data.answer,
                sources: data.sources,
                confidence: data.confidence
            };

            setMessages(prev => [...prev, botMsg]);

        } catch (err: any) {
            const errorMsg: Message = {
                role: 'assistant',
                content: `Error: ${err.response?.data?.error || err.message}. Please check if the backend is running.`
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setLoading(false);
        }
    };

    // Show loading state while auth is initializing
    if (authLoading) {
        return (
            <div className="h-[calc(100vh-100px)] flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                    <p className="text-slate-400">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    // Protected route handles redirects for non-authenticated users

    return (
        <div className="h-[calc(100vh-100px)] flex gap-6">

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col glass-card border border-blue-500/10 rounded-2xl overflow-hidden medical-shadow-lg">

                {/* Chat Header / Patient Context */}
                <div className="p-4 border-b border-blue-500/10 bg-gradient-to-r from-blue-500/5 to-cyan-500/5 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center text-blue-400 border border-blue-400/30">
                            <User className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="font-semibold text-white">Patient Context</h2>
                            <div className="flex items-center gap-2 text-xs text-slate-400">
                                <PatientSelector
                                    currentPatientId={patientId}
                                    onSelect={(id, name) => {
                                        setPatientId(id);
                                        setPatientName(name);
                                        setMessages(prev => [...prev, {
                                            role: 'assistant',
                                            content: `Switched context to **${name}** (${id}). Loading encrypted records...`
                                        }]);
                                    }}
                                />
                                <span className="text-blue-400 flex items-center gap-1 ml-2">
                                    <span className="status-indicator status-active"></span>
                                    Secure Session Active
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6" ref={scrollRef}>
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>

                            {/* Avatar */}
                            <div className={`w-12 h-12 rounded-full flex shrink-0 items-center justify-center border-2 shadow-lg ${msg.role === 'user' ? 'bg-gradient-to-br from-cyan-500/30 to-blue-500/30 text-cyan-300 border-cyan-400/50' : 'bg-gradient-to-br from-blue-500/30 to-cyan-500/30 text-blue-300 border-blue-400/50'
                                }`}>
                                {msg.role === 'user' ? <User className="w-6 h-6" /> : <Bot className="w-6 h-6" />}
                            </div>

                            {/* Message Container */}
                            <div className={`flex flex-col max-w-[75%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                {/* Role Label & Timestamp */}
                                <div className={`flex items-center gap-2 mb-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                    <span className={`text-sm font-semibold ${msg.role === 'user' ? 'text-cyan-300' : 'text-blue-300'}`}>
                                        {msg.role === 'user' ? 'Dr. Smith' : 'AI Clinical Assistant'}
                                    </span>
                                    <span className="text-xs text-slate-500">
                                        {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>

                                {/* Message Bubble */}
                                <div className={`px-6 py-4 rounded-2xl shadow-xl ${msg.role === 'user'
                                    ? 'bg-gradient-to-br from-cyan-600 to-blue-600 text-white rounded-tr-sm border border-cyan-400/20'
                                    : 'glass-card text-slate-100 rounded-tl-sm border border-blue-500/30 shadow-blue-500/10'
                                    }`}>
                                    <p className="text-[15px] leading-relaxed font-normal tracking-wide whitespace-pre-wrap">
                                        {msg.content}
                                    </p>
                                </div>

                                {/* Citations / Confidence */}
                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="mt-4 space-y-3 w-full animate-in fade-in slide-in-from-top-4 duration-500">
                                        <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg w-fit">
                                            <CheckCircle className="w-4 h-4 text-blue-400" />
                                            <span className="text-xs font-semibold text-blue-300 uppercase tracking-wider">
                                                Verified Sources
                                            </span>
                                            <span className="text-xs text-slate-400">
                                                • Confidence: {((msg.confidence || 0) * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                        <div className="grid gap-3">
                                            {msg.sources.map((src, i) => (
                                                <div key={i} className="glass-card border border-blue-500/20 rounded-xl p-4 hover:border-blue-400/50 hover:shadow-lg hover:shadow-blue-500/10 transition-all cursor-pointer group">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <FileText className="w-4 h-4 text-blue-400" />
                                                        <span className="text-xs font-semibold font-mono bg-blue-500/20 px-2 py-1 rounded-md border border-blue-500/30 text-blue-300">
                                                            {src.type}
                                                        </span>
                                                        <span className="text-xs text-slate-500 font-medium">{src.date}</span>
                                                        <div className="ml-auto">
                                                            <span className="text-xs text-slate-600 group-hover:text-blue-400 transition-colors">
                                                                {(src.similarity * 100).toFixed(0)}% match
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <p className="text-sm text-slate-400 leading-relaxed italic group-hover:text-slate-300 transition-colors">
                                                        "{src.snippet}"
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div className="flex gap-4">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500/30 to-cyan-500/30 flex shrink-0 items-center justify-center text-blue-300 border-2 border-blue-400/50 pulse-glow shadow-lg">
                                <Bot className="w-6 h-6" />
                            </div>
                            <div className="flex flex-col">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-sm font-semibold text-blue-300">AI Clinical Assistant</span>
                                    <span className="text-xs text-slate-500">
                                        {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                                <div className="glass-card px-6 py-4 rounded-2xl rounded-tl-sm border border-blue-500/30 flex items-center gap-3 shadow-xl shadow-blue-500/10">
                                    <div className="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                    <div className="w-2.5 h-2.5 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                    <div className="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                    <span className="text-sm text-slate-400 ml-2">Analyzing patient data...</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-5 bg-gradient-to-r from-blue-500/5 to-cyan-500/5 border-t border-blue-500/10">
                    <form onSubmit={handleSearch} className="relative">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Ask a clinical question about this patient..."
                            className="w-full glass-card border border-blue-500/20 rounded-xl py-4 pl-6 pr-14 text-[15px] text-slate-200 placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30 outline-none transition-all shadow-lg"
                        />
                        <button
                            type="submit"
                            disabled={loading || !query.trim()}
                            className="absolute right-3 top-3 p-2.5 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-400 hover:to-cyan-400 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all medical-shadow"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </form>
                    <p className="text-center text-xs text-slate-500 mt-3 flex items-center justify-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                        <span className="font-medium">AI-generated content. Always verify with original medical records.</span>
                    </p>
                </div>
            </div>

        </div>
    );
}
