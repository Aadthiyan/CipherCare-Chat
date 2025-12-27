'use client';

import { use, useState, useEffect } from 'react';
import { User, Calendar, Phone, Mail, Activity, Heart, Thermometer, Wind, Droplets, FileText, Pill, Download, Plus, Edit, ArrowLeft, Clock, Stethoscope, AlertTriangle, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';

type TabType = 'overview' | 'vitals' | 'medications' | 'history' | 'observations';

export default function PatientRecordPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const { axiosInstance } = useAuth();
    const [selectedTab, setSelectedTab] = useState<TabType>('overview');
    const [patient, setPatient] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Fetch patient details from API
    useEffect(() => {
        const fetchPatientDetails = async () => {
            try {
                setIsLoading(true);
                const response = await axiosInstance.get(`/api/v1/patients/${id}/details`);
                setPatient(response.data);
                setError(null);
            } catch (err: any) {
                console.error('Error fetching patient details:', err);
                if (err.response?.status === 404) {
                    setError(`Patient ${id} not found`);
                } else {
                    setError('Failed to load patient details');
                }
            } finally {
                setIsLoading(false);
            }
        };

        if (axiosInstance && id) {
            fetchPatientDetails();
        }
    }, [axiosInstance, id]);

    const getRiskColor = (level: string) => {
        switch (level) {
            case 'High': return 'bg-red-500/20 text-red-400 border-red-500/30';
            case 'Medium': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
            case 'Low': return 'bg-green-500/20 text-green-400 border-green-500/30';
            default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
        }
    };

    const getVitalStatus = (status: string) => {
        switch (status) {
            case 'normal': return 'text-green-400 bg-green-500/10 border-green-500/30';
            case 'elevated': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
            case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30';
            default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
        }
    };

    if (isLoading) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
                    <p className="text-slate-400">Loading patient details...</p>
                </div>
            </div>
        );
    }

    if (error || !patient) {
        return (
            <div className="h-full flex flex-col">
                <Link
                    href="/dashboard/records"
                    className="mb-4 flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors w-fit"
                >
                    <ArrowLeft className="w-4 h-4" />
                    <span className="text-sm font-medium">Back to Records</span>
                </Link>
                <div className="flex-1 flex items-center justify-center">
                    <div className="glass-card border border-red-500/30 rounded-xl p-8 text-center max-w-md">
                        <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
                        <h2 className="text-xl font-semibold text-white mb-2">Error Loading Patient</h2>
                        <p className="text-slate-400">{error || 'Patient not found'}</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            {/* Back Button */}
            <Link
                href="/dashboard/records"
                className="mb-4 flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors w-fit"
            >
                <ArrowLeft className="w-4 h-4" />
                <span className="text-sm font-medium">Back to Records</span>
            </Link>

            {/* Patient Header */}
            <div className="glass-card border border-blue-500/10 rounded-2xl p-6 mb-6">
                <div className="flex items-start justify-between mb-6">
                    <div className="flex gap-4">
                        {/* Avatar */}
                        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500/30 to-cyan-500/30 border-2 border-blue-400/50 flex items-center justify-center text-blue-300 font-bold text-2xl">
                            {patient.name?.split(' ').map((n: string) => n[0]).join('') || 'P'}
                        </div>

                        {/* Basic Info */}
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <h1 className="text-2xl font-bold text-white">{patient.name}</h1>
                                <span className="text-sm text-slate-500 font-mono">#{patient.id}</span>
                                <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getRiskColor(patient.riskLevel)}`}>
                                    {patient.riskLevel} Risk
                                </span>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-2 text-sm">
                                <div className="flex items-center gap-2 text-slate-400">
                                    <User className="w-4 h-4" />
                                    <span>{patient.age}yrs • {patient.gender}</span>
                                </div>
                                <div className="flex items-center gap-2 text-slate-400">
                                    <Calendar className="w-4 h-4" />
                                    <span>DOB: {patient.dob ? new Date(patient.dob).toLocaleDateString() : 'N/A'}</span>
                                </div>
                                <div className="flex items-center gap-2 text-slate-400">
                                    <FileText className="w-4 h-4" />
                                    <span>{patient.totalRecords || 0} records</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Additional Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-blue-500/10">
                    <div>
                        <p className="text-xs text-slate-500 mb-1">Primary Care Physician</p>
                        <p className="text-sm text-slate-200 font-medium flex items-center gap-2">
                            <Stethoscope className="w-4 h-4 text-blue-400" />
                            {patient.pcp || 'Not assigned'}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-slate-500 mb-1">Address</p>
                        <p className="text-sm text-slate-200 font-medium">{patient.address || 'N/A'}</p>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                <button
                    onClick={() => setSelectedTab('overview')}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all whitespace-nowrap ${selectedTab === 'overview'
                        ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-300 border border-blue-500/30'
                        : 'text-slate-400 hover:bg-blue-500/10 hover:text-blue-300 border border-transparent'
                        }`}
                >
                    <FileText className="w-4 h-4" />
                    Overview
                </button>
                <button
                    onClick={() => setSelectedTab('vitals')}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all whitespace-nowrap ${selectedTab === 'vitals'
                        ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-300 border border-blue-500/30'
                        : 'text-slate-400 hover:bg-blue-500/10 hover:text-blue-300 border border-transparent'
                        }`}
                >
                    <Activity className="w-4 h-4" />
                    Vitals ({patient.vitals?.length || 0})
                </button>
                <button
                    onClick={() => setSelectedTab('medications')}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all whitespace-nowrap ${selectedTab === 'medications'
                        ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-300 border border-blue-500/30'
                        : 'text-slate-400 hover:bg-blue-500/10 hover:text-blue-300 border border-transparent'
                        }`}
                >
                    <Pill className="w-4 h-4" />
                    Medications ({patient.medications?.length || 0})
                </button>
                <button
                    onClick={() => setSelectedTab('history')}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all whitespace-nowrap ${selectedTab === 'history'
                        ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-300 border border-blue-500/30'
                        : 'text-slate-400 hover:bg-blue-500/10 hover:text-blue-300 border border-transparent'
                        }`}
                >
                    <FileText className="w-4 h-4" />
                    Conditions ({patient.medicalHistory?.length || 0})
                </button>
                <button
                    onClick={() => setSelectedTab('observations')}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all whitespace-nowrap ${selectedTab === 'observations'
                        ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-300 border border-blue-500/30'
                        : 'text-slate-400 hover:bg-blue-500/10 hover:text-blue-300 border border-transparent'
                        }`}
                >
                    <Activity className="w-4 h-4" />
                    Observations ({patient.observations?.length || 0})
                </button>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto">
                {selectedTab === 'overview' && (
                    <div className="space-y-6">
                        {/* Summary Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="glass-card border border-blue-500/10 rounded-xl p-4">
                                <p className="text-xs text-slate-500 mb-1">Total Records</p>
                                <p className="text-2xl font-bold text-white">{patient.totalRecords || 0}</p>
                            </div>
                            <div className="glass-card border border-blue-500/10 rounded-xl p-4">
                                <p className="text-xs text-slate-500 mb-1">Vitals</p>
                                <p className="text-2xl font-bold text-white">{patient.vitals?.length || 0}</p>
                            </div>
                            <div className="glass-card border border-blue-500/10 rounded-xl p-4">
                                <p className="text-xs text-slate-500 mb-1">Medications</p>
                                <p className="text-2xl font-bold text-white">{patient.medications?.length || 0}</p>
                            </div>
                            <div className="glass-card border border-blue-500/10 rounded-xl p-4">
                                <p className="text-xs text-slate-500 mb-1">Conditions</p>
                                <p className="text-2xl font-bold text-white">{patient.medicalHistory?.length || 0}</p>
                            </div>
                        </div>

                        {/* Latest Vitals */}
                        {patient.vitals && patient.vitals.length > 0 && (
                            <div className="glass-card border border-blue-500/10 rounded-xl p-6">
                                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                    <Activity className="w-5 h-5 text-blue-400" />
                                    Latest Vitals
                                </h2>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {patient.vitals.slice(0, 6).map((vital: any, idx: number) => (
                                        <div key={idx} className="bg-slate-900/50 border border-blue-500/10 rounded-lg p-4">
                                            <p className="text-xs text-slate-400 mb-2">{vital.label}</p>
                                            <p className="text-xl font-bold text-white mb-1">
                                                {vital.value} <span className="text-sm text-slate-500 font-normal">{vital.unit}</span>
                                            </p>
                                            <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${getVitalStatus(vital.status)}`}>
                                                {vital.status}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {selectedTab === 'vitals' && (
                    <div className="glass-card border border-blue-500/10 rounded-xl p-6">
                        <h2 className="text-xl font-semibold text-white mb-6">Vital Signs</h2>
                        {patient.vitals && patient.vitals.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {patient.vitals.map((vital: any, idx: number) => (
                                    <div key={idx} className="bg-slate-900/50 border border-blue-500/10 rounded-xl p-5">
                                        <div className="mb-3">
                                            <p className="text-sm text-slate-400">{vital.label}</p>
                                            <p className="text-xs text-slate-600">{vital.lastUpdated ? new Date(vital.lastUpdated).toLocaleString() : 'N/A'}</p>
                                        </div>
                                        <p className="text-3xl font-bold text-white mb-2">
                                            {vital.value} <span className="text-lg text-slate-500 font-normal">{vital.unit}</span>
                                        </p>
                                        <span className={`inline-block px-3 py-1 rounded-lg text-sm font-medium border ${getVitalStatus(vital.status)}`}>
                                            {vital.status}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-slate-400 text-center py-8">No vital signs recorded</p>
                        )}
                    </div>
                )}

                {selectedTab === 'medications' && (
                    <div className="glass-card border border-blue-500/10 rounded-xl p-6">
                        <h2 className="text-xl font-semibold text-white mb-6">Active Medications</h2>
                        {patient.medications && patient.medications.length > 0 ? (
                            <div className="space-y-4">
                                {patient.medications.map((med: any, idx: number) => (
                                    <div key={idx} className="bg-slate-900/50 border border-blue-500/10 rounded-xl p-5">
                                        <h3 className="text-lg font-semibold text-white mb-2">{med.name}</h3>
                                        <div className="grid grid-cols-2 gap-4 text-sm">
                                            <div>
                                                <p className="text-slate-500">Status</p>
                                                <p className="text-slate-200">{med.status || 'Active'}</p>
                                            </div>
                                            <div>
                                                <p className="text-slate-500">Start Date</p>
                                                <p className="text-slate-200">{med.startDate ? new Date(med.startDate).toLocaleDateString() : 'N/A'}</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-slate-400 text-center py-8">No medications recorded</p>
                        )}
                    </div>
                )}

                {selectedTab === 'history' && (
                    <div className="glass-card border border-blue-500/10 rounded-xl p-6">
                        <h2 className="text-xl font-semibold text-white mb-6">Medical History</h2>
                        {patient.medicalHistory && patient.medicalHistory.length > 0 ? (
                            <div className="space-y-4">
                                {patient.medicalHistory.map((condition: any, idx: number) => (
                                    <div key={idx} className="bg-slate-900/50 border border-blue-500/10 rounded-xl p-5">
                                        <h3 className="text-lg font-semibold text-white mb-2">{condition.condition}</h3>
                                        <div className="grid grid-cols-3 gap-4 text-sm">
                                            <div>
                                                <p className="text-slate-500">Diagnosed</p>
                                                <p className="text-slate-200">{condition.diagnosedDate ? new Date(condition.diagnosedDate).toLocaleDateString() : 'N/A'}</p>
                                            </div>
                                            <div>
                                                <p className="text-slate-500">Status</p>
                                                <span className={`inline-block px-2 py-1 rounded text-xs ${condition.status === 'Active' ? 'bg-green-500/10 text-green-400' : 'bg-slate-500/10 text-slate-400'}`}>
                                                    {condition.status}
                                                </span>
                                            </div>
                                            <div>
                                                <p className="text-slate-500">Severity</p>
                                                <p className="text-slate-200">{condition.severity}</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-slate-400 text-center py-8">No medical history recorded</p>
                        )}
                    </div>
                )}

                {selectedTab === 'observations' && (
                    <div className="glass-card border border-blue-500/10 rounded-xl p-6">
                        <h2 className="text-xl font-semibold text-white mb-6">Clinical Observations</h2>
                        {patient.observations && patient.observations.length > 0 ? (
                            <div className="space-y-3">
                                {patient.observations.map((obs: any, idx: number) => (
                                    <div key={idx} className="bg-slate-900/50 border border-blue-500/10 rounded-lg p-4 flex justify-between items-center">
                                        <div>
                                            <p className="text-sm font-medium text-slate-200">{obs.name}</p>
                                            <p className="text-xs text-slate-500">{obs.date ? new Date(obs.date).toLocaleString() : 'N/A'}</p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-lg font-semibold text-white">{obs.value} <span className="text-sm text-slate-500">{obs.unit}</span></p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-slate-400 text-center py-8">No observations recorded</p>
                        )}
                    </div>
                )}
            </div>

            {/* Encryption Notice */}
            <div className="mt-6 glass-card border border-green-500/20 rounded-xl p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center shrink-0">
                    <AlertTriangle className="w-5 h-5 text-green-400" />
                </div>
                <div className="flex-1">
                    <p className="text-sm font-medium text-green-300">Encrypted Record</p>
                    <p className="text-xs text-slate-400">This patient record is end-to-end encrypted and HIPAA-compliant</p>
                </div>
            </div>
        </div>
    );
}
