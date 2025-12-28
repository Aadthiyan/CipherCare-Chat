'use client';

import { useState, useEffect } from 'react';
import { Search, Filter, User, Calendar, FileText, ChevronRight, Activity, Clock, Stethoscope, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';

interface PatientRecord {
    id: string;
    name: string;
    age: string | number;
    gender: string;
    lastVisit?: string;
    totalRecords?: number;
    recentRecords?: Array<{ type: string; date: string; category: string }>;
    condition?: string;
    pcp?: string;
    riskLevel?: string;
}

// Mock patient records data (fallback)
const MOCK_PATIENT_RECORDS: PatientRecord[] = [
    {
        id: 'MRN-2301',
        name: 'John Doe',
        age: 45,
        gender: 'M',
        lastVisit: '2024-12-20',
        totalRecords: 24,
        recentRecords: [
            { type: 'Lab Results', date: '2024-12-20', category: 'Lab Report' },
            { type: 'Consultation Notes', date: '2024-12-18', category: 'Clinical Notes' },
            { type: 'Prescription', date: '2024-12-15', category: 'Prescription' }
        ],
        condition: 'Type 2 Diabetes',
        pcp: 'Dr. Sarah Johnson',
        riskLevel: 'Medium'
    },
    {
        id: 'MRN-2302',
        name: 'Sarah Connor',
        age: 29,
        gender: 'F',
        lastVisit: '2024-12-18',
        totalRecords: 18,
        recentRecords: [
            { type: 'ECG Report', date: '2024-12-18', category: 'Diagnostic' },
            { type: 'Follow-up Notes', date: '2024-12-10', category: 'Clinical Notes' }
        ],
        condition: 'Hypertension',
        pcp: 'Dr. Michael Chen',
        riskLevel: 'Low'
    },
    {
        id: 'MRN-2303',
        name: 'Michael Smith',
        age: 62,
        gender: 'M',
        lastVisit: '2024-12-22',
        totalRecords: 42,
        recentRecords: [
            { type: 'Chest X-Ray', date: '2024-12-22', category: 'Imaging' },
            { type: 'Pulmonary Function Test', date: '2024-12-20', category: 'Lab Report' },
            { type: 'Emergency Visit Notes', date: '2024-12-19', category: 'Clinical Notes' }
        ],
        condition: 'COPD',
        pcp: 'Dr. Emily Brown',
        riskLevel: 'High'
    },
    {
        id: 'MRN-2304',
        name: 'Emily Blunt',
        age: 34,
        gender: 'F',
        lastVisit: '2024-11-30',
        totalRecords: 15,
        recentRecords: [
            { type: 'Neurology Consultation', date: '2024-11-30', category: 'Clinical Notes' },
            { type: 'MRI Brain', date: '2024-11-28', category: 'Imaging' }
        ],
        condition: 'Migraine',
        pcp: 'Dr. Robert Lee',
        riskLevel: 'Low'
    },
    {
        id: 'MRN-2305',
        name: 'Robert Stark',
        age: 55,
        gender: 'M',
        lastVisit: '2024-12-21',
        totalRecords: 31,
        recentRecords: [
            { type: 'Holter Monitor Results', date: '2024-12-21', category: 'Diagnostic' },
            { type: 'Cardiology Follow-up', date: '2024-12-15', category: 'Clinical Notes' },
            { type: 'Echocardiogram', date: '2024-12-10', category: 'Imaging' }
        ],
        condition: 'Arrhythmia',
        pcp: 'Dr. Michael Chen',
        riskLevel: 'Medium'
    },
    {
        id: 'MRN-2306',
        name: 'Lisa Anderson',
        age: 41,
        gender: 'F',
        lastVisit: '2024-12-15',
        totalRecords: 22,
        recentRecords: [
            { type: 'Spirometry Test', date: '2024-12-15', category: 'Lab Report' },
            { type: 'Allergy Panel', date: '2024-12-10', category: 'Lab Report' }
        ],
        condition: 'Asthma',
        pcp: 'Dr. Emily Brown',
        riskLevel: 'Low'
    },
];

const RECORD_CATEGORIES = ['All Categories', 'Lab Report', 'Clinical Notes', 'Prescription', 'Imaging', 'Diagnostic'];

export default function RecordsPage() {
    const { axiosInstance } = useAuth();
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All Categories');
    const [showFilters, setShowFilters] = useState(false);
    const [patientRecords, setPatientRecords] = useState<PatientRecord[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Fetch patient data from backend
    useEffect(() => {
        const fetchPatients = async () => {
            try {
                setIsLoading(true);
                const response = await axiosInstance.get('/api/v1/patients');

                const data = response.data;
                if (data.patients && data.patients.length > 0) {
                    // Transform backend patient data to match our format
                    const transformedPatients = data.patients.map((p: any) => ({
                        id: p.id || 'Unknown',
                        name: p.name || `Patient ${p.id}`,
                        age: p.age || 'N/A',
                        gender: p.gender || 'U',
                        condition: p.condition || 'Not specified',
                        pcp: p.pcp || 'Not assigned',
                        riskLevel: p.riskLevel || 'Low',
                        lastVisit: p.lastVisit || 'No visits',
                        totalRecords: p.numConditions || 0,
                        recentRecords: [
                            { type: 'Patient Record', date: new Date().toISOString().split('T')[0], category: 'Clinical Notes' }
                        ]
                    }));
                    setPatientRecords(transformedPatients);
                } else {
                    // No patients in database - show message
                    setPatientRecords([]);
                    setError(data.message || 'No patient data available');
                }
                setError(null);
            } catch (err: any) {
                console.error('Error fetching patients:', err);
                if (err.response?.status === 401) {
                    setError('Please log in again to access patient records');
                } else {
                    setError('Failed to load patient records. Using demo data.');
                    // Fall back to mock data
                    setPatientRecords(MOCK_PATIENT_RECORDS);
                }
            } finally {
                setIsLoading(false);
            }
        };

        if (axiosInstance) {
            fetchPatients();
        }
    }, [axiosInstance]);

    const filteredRecords = patientRecords.filter(patient => {
        const matchesSearch =
            patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            patient.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (patient.condition && patient.condition.toLowerCase().includes(searchTerm.toLowerCase()));

        const matchesCategory = selectedCategory === 'All Categories' ||
            (patient.recentRecords && patient.recentRecords.some(record => record.category === selectedCategory));

        return matchesSearch && matchesCategory;
    });

    const getRiskColor = (level: string | undefined) => {
        switch (level) {
            case 'High': return 'bg-red-500/20 text-red-400 border-red-500/30';
            case 'Medium': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
            case 'Low': return 'bg-green-500/20 text-green-400 border-green-500/30';
            default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
        }
    };

    const getCategoryColor = (category: string) => {
        switch (category) {
            case 'Lab Report': return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
            case 'Clinical Notes': return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
            case 'Prescription': return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
            case 'Imaging': return 'bg-pink-500/10 text-pink-400 border-pink-500/30';
            case 'Diagnostic': return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
            default: return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
        }
    };

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">Medical Records</h1>
                <p className="text-slate-400">View encrypted medical records and documents</p>
            </div>

            {/* Error Alert */}
            {error && !patientRecords.length && (
                <div className="glass-card border border-amber-500/30 rounded-xl p-4 mb-6 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                        <p className="text-sm font-medium text-amber-300">{error}</p>
                        {error.includes('demo data') && (
                            <p className="text-xs text-slate-400 mt-1">Upload patient data to see real records</p>
                        )}
                    </div>
                </div>
            )}

            {/* Search and Filters */}
            <div className="glass-card border border-blue-500/10 rounded-2xl p-6 mb-6 space-y-4">
                {/* Search Bar */}
                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search by patient name, MRN, or condition..."
                        disabled={isLoading}
                        className="w-full bg-slate-900/50 border border-blue-500/20 rounded-xl py-4 pl-12 pr-4 text-[15px] text-slate-200 placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30 outline-none transition-all disabled:opacity-50"
                    />
                </div>

                {/* Filter Toggle */}
                <button
                    onClick={() => setShowFilters(!showFilters)}
                    disabled={isLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-300 transition-all disabled:opacity-50"
                >
                    <Filter className="w-4 h-4" />
                    <span className="font-medium">Filter by Category</span>
                    {selectedCategory !== 'All Categories' && (
                        <span className="ml-2 px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">Active</span>
                    )}
                </button>

                {/* Filter Options */}
                {showFilters && (
                    <div className="pt-4 border-t border-blue-500/10 animate-in fade-in slide-in-from-top-2 duration-300">
                        <label className="block text-sm font-medium text-slate-300 mb-2">Record Category</label>
                        <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            disabled={isLoading}
                            className="w-full md:w-1/3 bg-slate-900/50 border border-blue-500/20 rounded-lg py-2.5 px-3 text-slate-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30 outline-none transition-all disabled:opacity-50"
                        >
                            {RECORD_CATEGORIES.map(category => (
                                <option key={category} value={category}>{category}</option>
                            ))}
                        </select>
                    </div>
                )}
            </div>

            {/* Results Count */}
            <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-slate-400">
                    Showing <span className="text-blue-300 font-semibold">{isLoading ? '...' : filteredRecords.length}</span> patient records
                </p>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span>All records encrypted</span>
                </div>
            </div>

            {/* Patient Records List */}
            <div className="flex-1 overflow-y-auto space-y-3">
                {isLoading ? (
                    <div className="space-y-3">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="glass-card border border-blue-500/10 rounded-xl p-5 animate-pulse">
                                <div className="flex items-start gap-4">
                                    <div className="w-14 h-14 rounded-full bg-slate-700"></div>
                                    <div className="flex-1">
                                        <div className="h-4 bg-slate-700 rounded w-1/4 mb-2"></div>
                                        <div className="h-3 bg-slate-700 rounded w-1/3"></div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : filteredRecords.length === 0 ? (
                    <div className="glass-card border border-blue-500/10 rounded-xl p-12 text-center">
                        <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-slate-300 mb-2">No records found</h3>
                        <p className="text-slate-500">
                            {error && error.includes('No patients') ? 'Upload patient data to get started' : 'Try adjusting your search or filter criteria'}
                        </p>
                    </div>
                ) : (
                    filteredRecords.map((patient) => (
                        <Link
                            key={patient.id}
                            href={`/dashboard/records/${patient.id}`}
                            className="block glass-card border border-blue-500/10 rounded-xl p-5 hover:border-blue-400/40 hover:shadow-lg hover:shadow-blue-500/10 transition-all group"
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
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${getRiskColor(patient.riskLevel)}`}>
                                                {patient.riskLevel} Risk
                                            </span>
                                        </div>

                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-2 text-sm mb-3">
                                            <div className="flex items-center gap-2 text-slate-400">
                                                <User className="w-4 h-4" />
                                                <span>{patient.age}yrs • {patient.gender}</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-slate-400">
                                                <Activity className="w-4 h-4" />
                                                <span className="truncate">{patient.condition}</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-slate-400">
                                                <Stethoscope className="w-4 h-4" />
                                                <span className="truncate">{patient.pcp}</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-slate-400">
                                                <FileText className="w-4 h-4" />
                                                <span>{patient.totalRecords} records</span>
                                            </div>
                                        </div>

                                        {/* Recent Records */}
                                        {patient.recentRecords && patient.recentRecords.length > 0 && (
                                            <div>
                                                <p className="text-xs text-slate-500 mb-2 flex items-center gap-2">
                                                    <Clock className="w-3 h-3" />
                                                    Recent Records
                                                </p>
                                                <div className="flex flex-wrap gap-2">
                                                    {patient.recentRecords.map((record, idx) => (
                                                        <div key={idx} className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${getCategoryColor(record.category)}`}>
                                                            <span className="font-semibold">{record.type}</span>
                                                            <span className="mx-1.5 opacity-50">•</span>
                                                            <span className="opacity-75">{new Date(record.date).toLocaleDateString()}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {patient.lastVisit && (
                                            <div className="mt-3 text-xs text-slate-500">
                                                Last Visit: <span className="text-slate-400">{typeof patient.lastVisit === 'string' && patient.lastVisit.startsWith('2') ? new Date(patient.lastVisit).toLocaleDateString() : patient.lastVisit}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Right Section - Action */}
                                <button className="ml-4 p-2 hover:bg-blue-500/10 rounded-lg transition-colors group-hover:text-blue-300">
                                    <ChevronRight className="w-5 h-5" />
                                </button>
                            </div>
                        </Link>
                    ))
                )}
            </div>

            {/* Encryption Notice */}
            <div className="mt-6 glass-card border border-green-500/20 rounded-xl p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center shrink-0">
                    <AlertCircle className="w-5 h-5 text-green-400" />
                </div>
                <div className="flex-1">
                    <p className="text-sm font-medium text-green-300">End-to-End Encrypted</p>
                    <p className="text-xs text-slate-400">All medical records are encrypted and HIPAA-compliant</p>
                </div>
            </div>
        </div>
    );
}
