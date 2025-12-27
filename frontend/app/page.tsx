'use client';

import Link from 'next/link';
import { Heart, Activity, Lock, Shield, Stethoscope, Users, FileText, Zap } from 'lucide-react';

// Force dynamic rendering to avoid static generation memory issues
export const dynamic = 'force-dynamic';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0a0e1a] flex flex-col relative overflow-hidden medical-grid">
      {/* Animated Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-3xl float-animation"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-3xl float-animation" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-[40%] left-[50%] w-[400px] h-[400px] bg-teal-500/5 rounded-full blur-3xl"></div>
      </div>

      {/* Navbar */}
      <nav className="z-10 px-8 py-6 flex justify-between items-center border-b border-white/5 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Heart className="w-8 h-8 text-blue-400 heartbeat" fill="currentColor" />
            <div className="absolute inset-0 w-8 h-8 text-blue-400 opacity-30 blur-sm">
              <Heart className="w-8 h-8" fill="currentColor" />
            </div>
          </div>
          <span className="text-2xl font-bold text-gradient-medical">
            CiperCare
          </span>
          <span className="ml-2 px-2 py-0.5 bg-blue-500/10 border border-blue-500/30 rounded text-xs text-blue-300 font-medium">
            Healthcare AI
          </span>
        </div>
        <Link
          href="/auth/login"
          className="px-6 py-2.5 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-400 hover:to-cyan-400 text-white font-semibold rounded-full transition-all shadow-lg shadow-blue-500/20 flex items-center gap-2"
        >
          <Shield className="w-4 h-4" />
          Clinician Portal
        </Link>
      </nav>

      {/* Hero Content */}
      <main className="flex-1 flex flex-col items-center justify-center text-center z-10 px-4 py-12">
        <div className="max-w-5xl space-y-10">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full glass-card text-slate-200 text-sm mb-4 border border-blue-500/20">
            <Lock className="w-4 h-4 text-blue-400" />
            <span className="font-medium">HIPAA-Compliant</span>
            <span className="w-1 h-1 rounded-full bg-blue-400"></span>
            <span className="font-medium">End-to-End Encrypted</span>
            <span className="w-1 h-1 rounded-full bg-blue-400"></span>
            <span className="font-medium">Zero-Trust Architecture</span>
          </div>

          {/* Main Heading */}
          <div className="space-y-6">
            <h1 className="text-7xl font-bold tracking-tight text-white leading-tight">
              Intelligent Healthcare
              <br />
              <span className="text-gradient-medical">
                Clinical Decision Support
              </span>
            </h1>

            <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
              Empower clinicians with AI-driven insights from encrypted patient records.
              Advanced RAG technology with Private LLMs ensures secure, instant access to critical medical information.
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="pt-6 flex gap-4 justify-center flex-wrap">
            <Link
              href="/auth/login"
              className="group px-8 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-400 hover:to-cyan-400 text-white font-bold rounded-xl transition-all shadow-xl shadow-blue-500/30 flex items-center gap-3"
            >
              <Activity className="w-5 h-5 group-hover:scale-110 transition-transform" />
              Access Dashboard
            </Link>
            <Link
              href="/auth/signup"
              className="px-8 py-4 glass-card hover:border-blue-400/50 text-blue-300 hover:text-blue-200 font-bold rounded-xl transition-all flex items-center gap-3 border border-blue-500/30"
            >
              <Users className="w-5 h-5" />
              Request Access
            </Link>
          </div>

          {/* Feature Pills */}
          <div className="pt-12 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <FeatureCard
              icon={<Stethoscope className="w-6 h-6" />}
              title="Clinical Intelligence"
              description="AI-powered analysis of patient records for faster, more accurate diagnoses"
            />
            <FeatureCard
              icon={<Shield className="w-6 h-6" />}
              title="Military-Grade Security"
              description="Zero-knowledge encryption ensures patient data remains completely private"
            />
            <FeatureCard
              icon={<Zap className="w-6 h-6" />}
              title="Real-Time Insights"
              description="Instant retrieval and analysis of medical records with sub-second response"
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 text-center text-slate-500 text-sm border-t border-white/5 backdrop-blur-sm z-10">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Heart className="w-4 h-4 text-blue-500" fill="currentColor" />
          <span className="text-slate-400">Trusted by Healthcare Professionals Worldwide</span>
        </div>
        <p>&copy; 2025 CiperCare. HIPAA Compliant • SOC 2 Type II Certified • Authorized Personnel Only</p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="glass-card p-6 rounded-2xl hover:border-blue-400/30 transition-all group cursor-pointer">
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center text-blue-400 mb-4 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}
