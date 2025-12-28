'use client';

import { useState, useEffect } from 'react';
import { Search, Filter, User, Calendar, Activity, Phone, Mail, MapPin, ChevronRight, AlertCircle, CheckCircle2, Clock, Stethoscope, Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

// Patient interface
interface Patient {
    id: string;
    name: string;
    age: string | number;
    gender: string;
    dob: string;
    phone: string;
    email: string;
    address: string;
    condition: string;
    careProgram: string;
    lastVisit: string;
    nextAppointment: string;
    status: string;
    riskLevel: string;
    pcp: string;
    numConditions?: number;
    numMedications?: number;
}


const CARE_PROGRAMS = ['All Programs', 'Diabetes Management', 'Cardiology Care', 'Respiratory Care', 'Neurology'];
const CONDITIONS = ['All Conditions', 'Type 2 Diabetes', 'Hypertension', 'COPD', 'Migraine', 'Arrhythmia', 'Asthma'];
const RISK_LEVELS = ['All Levels', 'Low', 'Medium', 'High'];

export default function PatientsPage() {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCareProgram, setSelectedCareProgram] = useState('All Programs');
    const [selectedCondition, setSelectedCondition] = useState('All Conditions');
    const [selectedRiskLevel, setSelectedRiskLevel] = useState('All Levels');
    const [showFilters, setShowFilters] = useState(false);
    const [patients, setPatients] = useState<Patient[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [usingRealData, setUsingRealData] = useState(false);

    // Fetch patients from backend
    useEffect(() => {
        const fetchPatients = async () => {
            setLoading(true);
            setError(null);
            
            try {
                const token = localStorage.getItem('access_token');
                console.log('🔑 Token check:', token ? 'Found' : 'NOT FOUND');
                
                if (!token) {
                    console.log('❌ No auth token found');
                    setError('Please login to view patients');
                    setPatients([]);
                    setUsingRealData(false);
                    setLoading(false);
                    return;
                }

                console.log('📡 Fetching patients from API...');
                const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
                const response = await fetch(`${backendUrl}/api/v1/patients?limit=500`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                console.log('📥 Response status:', response.status);

                if (response.ok) {
                    const data = await response.json();
                    console.log('📦 Response data:', data);
                    
                    if (data.patients && data.patients.length > 0) {
                        console.log('✅ Loaded', data.patients.length, 'patients from database');
                        console.log('First patient:', data.patients[0]);
                        setPatients(data.patients);
                        setUsingRealData(true);
                    } else {
                        console.log('⚠️ No patients in database response');
                        setError('No patients found in database');
                        setPatients([]);
                        setUsingRealData(false);
                    }
                } else {
                    const errorText = await response.text();
                    console.warn('❌ Failed to fetch patients:', response.status, errorText);
                    setError(`Failed to fetch patients: ${response.status}`);
                    setPatients([]);
                    setUsingRealData(false);
                }
            } catch (err) {
                console.error('💥 Error fetching patients:', err);
                setError('Database unavailable. Please check connection.');
                setPatients([]);
                setUsingRealData(false);
            } finally {
                setLoading(false);
            }
        };

        fetchPatients();
    }, []);

    const filteredPatients = patients.filter(patient => {
        const matchesSearch =
            patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            patient.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            patient.phone.includes(searchTerm) ||
            patient.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
            patient.age.toString().includes(searchTerm);

        const matchesCareProgram = selectedCareProgram === 'All Programs' || patient.careProgram === selectedCareProgram;
        const matchesCondition = selectedCondition === 'All Conditions' || patient.condition === selectedCondition;
        const matchesRiskLevel = selectedRiskLevel === 'All Levels' || patient.riskLevel === selectedRiskLevel;

        return matchesSearch && matchesCareProgram && matchesCondition && matchesRiskLevel;
    });

    const getRiskColor = (level: string) => {
        switch (level) {
            case 'High': return 'bg-red-500/20 text-red-400 border-red-500/30';
            case 'Medium': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
            case 'Low': return 'bg-green-500/20 text-green-400 border-green-500/30';
            default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'Active': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
            case 'Critical': return <AlertCircle className="w-4 h-4 text-red-400" />;
            case 'Inactive': return <Clock className="w-4 h-4 text-slate-400" />;
            default: return null;
        }
    };

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="mb-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Patient Directory</h1>
                        <p className="text-slate-400">Search and manage patient records with advanced filtering</p>
                    </div>
                    {usingRealData && (
                        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-lg">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                            <span className="text-sm text-green-400 font-medium">Live Data ({patients.length} patients)</span>
                        </div>
                    )}
                    {!usingRealData && !loading && (
                        <div className="flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                            <AlertCircle className="w-4 h-4 text-amber-400" />
                            <span className="text-sm text-amber-400 font-medium">Sample Data</span>
                        </div>
                    )}
                    {loading && (
                        <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                            <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                            <span className="text-sm text-blue-400 font-medium">Loading...</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Search and Filters */}
            <div className="glass-card border border-blue-500/10 rounded-2xl p-6 mb-6 space-y-4">
                {/* Search Bar */}
                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search by name, MRN, phone, email, or age..."
                        className="w-full bg-slate-900/50 border border-blue-500/20 rounded-xl py-4 pl-12 pr-4 text-[15px] text-slate-200 placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30 outline-none transition-all"
                    />
                </div>

                {/* Filter Toggle */}
                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-300 transition-all"
                >
                    <Filter className="w-4 h-4" />
                    <span className="font-medium">Advanced Filters</span>
                    {(selectedCareProgram !== 'All Programs' || selectedCondition !== 'All Conditions' || selectedRiskLevel !== 'All Levels') && (
                        <span className="ml-2 px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">Active</span>
                    )}
                </button>

                {/* Filter Options */}
                {showFilters && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-blue-500/10 animate-in fade-in slide-in-from-top-2 duration-300">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">Care Program</label>
                            <select
                                value={selectedCareProgram}
                                onChange={(e) => setSelectedCareProgram(e.target.value)}
                                className="w-full bg-slate-900/50 border border-blue-500/20 rounded-lg py-2.5 px-3 text-slate-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30 outline-none transition-all"
                            >
                                {CARE_PROGRAMS.map(program => (
                                    <option key={program} value={program}>{program}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">Medical Condition</label>
                            <select
                                value={selectedCondition}
                                onChange={(e) => setSelectedCondition(e.target.value)}
                                className="w-full bg-slate-900/50 border border-blue-500/20 rounded-lg py-2.5 px-3 text-slate-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30 outline-none transition-all"
                            >
                                {CONDITIONS.map(condition => (
                                    <option key={condition} value={condition}>{condition}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">Risk Level</label>
                            <select
                                value={selectedRiskLevel}
                                onChange={(e) => setSelectedRiskLevel(e.target.value)}
                                className="w-full bg-slate-900/50 border border-blue-500/20 rounded-lg py-2.5 px-3 text-slate-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30 outline-none transition-all"
                            >
                                {RISK_LEVELS.map(level => (
                                    <option key={level} value={level}>{level}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                )}
            </div>

            {/* Results Count */}
            <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-slate-400">
                    Showing <span className="text-blue-300 font-semibold">{filteredPatients.length}</span> of <span className="text-slate-300">{patients.length}</span> patients
                </p>
            </div>

            {/* Patient List */}
            <div className="flex-1 overflow-y-auto space-y-3">
                {filteredPatients.map((patient) => (
                    <div
                        key={patient.id}
                        className="glass-card border border-blue-500/10 rounded-xl p-5 hover:border-blue-400/40 hover:shadow-lg hover:shadow-blue-500/10 transition-all cursor-pointer group"
                    >
                        <div className="flex items-start justify-between">
                            {/* Left Section - Patient Info */}
                            <div className="flex gap-4 flex-1">
                                {/* Avatar */}
                                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500/30 to-cyan-500/30 border-2 border-blue-400/50 flex items-center justify-center text-blue-300 font-bold text-lg shrink-0">
                                    {patient.name.split(' ').map(n => n[0]).join('')}
                                </div>

                                {/* Details */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-3 mb-2">
                                        <h3 className="text-lg font-semibold text-white group-hover:text-blue-300 transition-colors">
                                            {patient.name}
                                        </h3>
                                        <span className="text-sm text-slate-500 font-mono">#{patient.id}</span>
                                        {getStatusIcon(patient.status)}
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${getRiskColor(patient.riskLevel)}`}>
                                            {patient.riskLevel} Risk
                                        </span>
                                    </div>

                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-2 text-sm">
                                        <div className="flex items-center gap-2 text-slate-400">
                                            <User className="w-4 h-4" />
                                            <span>{patient.age}yrs • {patient.gender}</span>
                                        </div>
                                        <div className="flex items-center gap-2 text-slate-400">
                                            <Phone className="w-4 h-4" />
                                            <span>{patient.phone}</span>
                                        </div>
                                        <div className="flex items-center gap-2 text-slate-400">
                                            <Activity className="w-4 h-4" />
                                            <span className="truncate">{patient.condition}</span>
                                        </div>
                                        <div className="flex items-center gap-2 text-slate-400">
                                            <Stethoscope className="w-4 h-4" />
                                            <span className="truncate">{patient.pcp}</span>
                                        </div>
                                    </div>

                                    <div className="mt-3 flex items-center gap-4 text-xs">
                                        <span className="px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-300">
                                            {patient.careProgram}
                                        </span>
                                        <span className="text-slate-500">
                                            Last Visit: <span className="text-slate-400">{new Date(patient.lastVisit).toLocaleDateString()}</span>
                                        </span>
                                        <span className="text-slate-500">
                                            Next: <span className="text-blue-400">{new Date(patient.nextAppointment).toLocaleDateString()}</span>
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Right Section - Action */}
                            <button className="ml-4 p-2 hover:bg-blue-500/10 rounded-lg transition-colors group-hover:text-blue-300">
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                ))}

                {filteredPatients.length === 0 && (
                    <div className="glass-card border border-blue-500/10 rounded-xl p-12 text-center">
                        <User className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-slate-300 mb-2">No patients found</h3>
                        <p className="text-slate-500">Try adjusting your search or filter criteria</p>
                    </div>
                )}
            </div>
        </div>
    );
}
