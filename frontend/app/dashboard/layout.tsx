'use client';

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    Users,
    FileText,
    Settings,
    LogOut,
    Heart
} from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { ProtectedRoute } from '@/components/protected-route';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, logout, isLoading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();

    const handleLogout = async () => {
        try {
            await logout();
            router.push('/');
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

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

    return (
        <ProtectedRoute>
            <div className="flex h-screen bg-[#0a0e1a] text-slate-100 overflow-hidden medical-grid">
                {/* Sidebar */}
                <aside className="w-64 glass-card border-r border-blue-500/10 flex flex-col">
                    <div className="p-6 flex items-center gap-3 border-b border-blue-500/10">
                        <div className="relative">
                            <Heart className="w-8 h-8 text-blue-400 heartbeat" fill="currentColor" />
                            <div className="absolute inset-0 w-8 h-8 text-blue-400 opacity-30 blur-sm">
                                <Heart className="w-8 h-8" fill="currentColor" />
                            </div>
                        </div>
                        <span className="font-bold text-xl tracking-tight text-gradient-medical">CiperCare</span>
                    </div>

                    <nav className="flex-1 p-4 space-y-2">
                        <NavLink href="/dashboard" icon={<LayoutDashboard />} label="Overview" active={pathname === '/dashboard'} />
                        <NavLink href="/dashboard/patients" icon={<Users />} label="Patients" active={pathname === '/dashboard/patients'} />
                        <NavLink href="/dashboard/records" icon={<FileText />} label="Records" active={pathname === '/dashboard/records'} />
                        <NavLink href="/dashboard/settings" icon={<Settings />} label="Settings" active={pathname === '/dashboard/settings'} />
                    </nav>

                    <div className="p-4 border-t border-blue-500/10">
                        <div className="flex items-center gap-3 mb-4 px-2">
                            <div className="w-10 h-10 rounded-full border border-blue-400/30 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center">
                                <span className="text-sm font-bold text-blue-300">
                                    {user?.full_name.split(' ').map(n => n[0]).join('').toUpperCase()}
                                </span>
                            </div>
                            <div className="flex-1 overflow-hidden">
                                <p className="text-sm font-medium truncate text-white">{user?.full_name}</p>
                                <p className="text-xs text-blue-400 truncate capitalize">{user?.roles[0]}</p>
                            </div>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors w-full border border-red-500/20 hover:border-red-500/40"
                        >
                            <LogOut className="w-4 h-4" />
                            Sign Out
                        </button>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 overflow-y-auto relative">
                    {/* Background Glows */}
                    <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
                        <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-3xl"></div>
                        <div className="absolute bottom-[-20%] left-[-10%] w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-3xl"></div>
                    </div>

                    <div className="p-8">
                        {children}
                    </div>
                </main>
            </div>
        </ProtectedRoute>
    );
}

function NavLink({ href, icon, label, active = false }: { href: string, icon: React.ReactNode, label: string, active?: boolean }) {
    return (
        <Link
            href={href}
            className={`group flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${active
                ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-300 border border-blue-500/30 medical-shadow'
                : 'text-slate-400 hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-cyan-500/10 hover:text-blue-200 border border-transparent hover:border-blue-500/20'
                }`}
        >
            <span className={`w-5 h-5 transition-transform duration-200 ${active ? '' : 'group-hover:scale-110'}`}>
                {icon}
            </span>
            <span className="font-medium">{label}</span>
        </Link>
    );
}
