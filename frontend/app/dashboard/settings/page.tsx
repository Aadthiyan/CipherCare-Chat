'use client';

export default function SettingsPage() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-bold text-white mb-2">Settings</h1>
                <p className="text-slate-400">Manage your account and security preferences.</p>
            </div>

            <div className="max-w-2xl space-y-6">
                <div className="bg-slate-900/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
                    <h3 className="text-lg font-bold text-white mb-4">Security & Encryption</h3>
                    <div className="space-y-3 text-sm">
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Encryption Status</span>
                            <span className="text-emerald-400 font-medium">✓ Vault Transit Active</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Algorithm</span>
                            <span className="text-slate-400">AES-256-GCM96</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Last Key Rotation</span>
                            <span className="text-slate-400">2025-12-23</span>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-900/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
                    <h3 className="text-lg font-bold text-white mb-4">Account</h3>
                    <div className="space-y-3">
                        <button className="w-full px-4 py-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 rounded-lg border border-emerald-500/50 transition-all">
                            Change Password
                        </button>
                        <button className="w-full px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-white/10 transition-all">
                            Two-Factor Authentication
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
