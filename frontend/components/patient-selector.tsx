'use client';

import * as React from 'react';
import { Search, Filter, User, Calendar, Activity, ChevronRight, Check } from 'lucide-react';
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface Patient {
    id: string;
    name: string;
    age: string | number;
    gender: string;
    condition: string;
    status: string;
    careProgram?: string;
    numConditions?: number;
    numMedications?: number;
}

interface PatientSelectorProps {
    currentPatientId: string;
    onSelect: (patientId: string, patientName: string) => void;
}

export function PatientSelector({ currentPatientId, onSelect }: PatientSelectorProps) {
    const [open, setOpen] = React.useState(false);
    const [searchTerm, setSearchTerm] = React.useState('');
    const [filterDept, setFilterDept] = React.useState<string | null>(null);
    const [patients, setPatients] = React.useState<Patient[]>([]);
    const [loading, setLoading] = React.useState(false);

    // Fetch patients from API when dialog opens
    React.useEffect(() => {
        if (open && patients.length === 0) {
            const fetchPatients = async () => {
                setLoading(true);
                try {
                    const token = localStorage.getItem('access_token');
                    if (!token) {
                        console.log('No auth token found');
                        return;
                    }

                    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
                    const response = await fetch(`${backendUrl}/api/v1/patients?limit=250`, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                    });

                    if (response.ok) {
                        const data = await response.json();
                        if (data.patients && data.patients.length > 0) {
                            // Transform to match expected format
                            const transformedPatients = data.patients.map((p: any) => ({
                                id: p.id,
                                name: p.name,
                                age: p.age,
                                gender: p.gender,
                                condition: p.condition || 'N/A',
                                status: p.status || 'Active',
                                careProgram: p.careProgram,
                                numConditions: p.numConditions,
                                numMedications: p.numMedications,
                            }));
                            setPatients(transformedPatients);
                        }
                    }
                } catch (err) {
                    console.error('Error fetching patients:', err);
                } finally {
                    setLoading(false);
                }
            };

            fetchPatients();
        }
    }, [open]);

    const filteredPatients = patients.filter(p => {
        const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            p.id.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesDept = filterDept ? p.careProgram === filterDept : true;
        return matchesSearch && matchesDept;
    });

    const selectedPatient = patients.find(p => p.id === currentPatientId);

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" className="w-[300px] justify-between border-blue-500/20 bg-slate-900/50 hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-cyan-500/10 hover:border-blue-400/40 text-slate-200 transition-all duration-200">
                    <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-blue-400" />
                        <span className="truncate">{selectedPatient ? `${selectedPatient.name} (${selectedPatient.id})` : 'Select Patient...'}</span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-500 opacity-50" />
                </Button>
            </DialogTrigger>

            <DialogContent className="sm:max-w-[600px] bg-slate-950 border-slate-800 text-slate-100 p-0 overflow-hidden gap-0">
                <DialogHeader className="p-4 border-b border-slate-800 bg-slate-900/50">
                    <DialogTitle>Select Patient Context</DialogTitle>
                </DialogHeader>

                <div className="p-4 border-b border-slate-800 bg-slate-900/20 space-y-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                        <Input
                            placeholder="Search by name or MRN..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-9 bg-slate-900 border-slate-800 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30 transition-all"
                        />
                    </div>

                    <div className="flex gap-2">
                        {loading ? (
                            <span className="text-sm text-slate-400">Loading patients...</span>
                        ) : (
                            <>
                                <Badge
                                    variant={!filterDept ? 'default' : 'outline'}
                                    className={cn(
                                        "cursor-pointer transition-all duration-200",
                                        !filterDept ? "bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-400 hover:to-cyan-400 border-transparent text-white" : "text-slate-400 border-slate-700 hover:border-blue-400 hover:text-blue-300"
                                    )}
                                    onClick={() => setFilterDept(null)}
                                >
                                    All
                                </Badge>
                            </>
                        )}
                    </div>
                </div>

                <ScrollArea className="h-[400px]">
                    <div className="divide-y divide-slate-800">
                        {filteredPatients.map(patient => (
                            <div
                                key={patient.id}
                                onClick={() => {
                                    onSelect(patient.id, patient.name);
                                    setOpen(false);
                                }}
                                className={cn(
                                    "p-4 flex items-center justify-between cursor-pointer hover:bg-gradient-to-r hover:from-blue-500/10 hover:to-cyan-500/10 transition-all duration-200 group",
                                    currentPatientId === patient.id ? "bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border-l-2 border-blue-400" : ""
                                )}
                            >
                                <div className="flex items-center gap-4">
                                    <div className={cn(
                                        "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-200",
                                        currentPatientId === patient.id ? "bg-gradient-to-br from-blue-500 to-cyan-500 text-white" : "bg-slate-800 text-slate-400 group-hover:bg-gradient-to-br group-hover:from-blue-500/20 group-hover:to-cyan-500/20 group-hover:text-blue-300"
                                    )}>
                                        {patient.name.split(' ').map(n => n[0]).join('')}
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-slate-200 group-hover:text-blue-300 transition-colors duration-200">
                                            {patient.name}
                                            <span className="ml-2 text-xs text-slate-500 font-normal">#{patient.id}</span>
                                        </h4>
                                        <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                                            <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {patient.age}yrs / {patient.gender}</span>
                                            <span className="w-1 h-1 rounded-full bg-slate-600" />
                                            <span className="flex items-center gap-1"><Activity className="w-3 h-3" /> {patient.condition}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="text-right">
                                    <Badge variant="outline" className={cn(
                                        "border-0",
                                        patient.status === 'Critical' ? "bg-red-500/10 text-red-400" :
                                            patient.status === 'Admitted' ? "bg-blue-500/10 text-blue-400" : "bg-slate-800 text-slate-400"
                                    )}>
                                        {patient.status}
                                    </Badge>
                                    {currentPatientId === patient.id && <Check className="w-4 h-4 text-blue-400 ml-auto mt-2" />}
                                </div>
                            </div>
                        ))}

                        {filteredPatients.length === 0 && !loading && (
                            <div className="p-8 text-center text-slate-500">
                                {patients.length === 0 ? 'Please login to view patients' : 'No patients found.'}
                            </div>
                        )}
                        {loading && (
                            <div className="p-8 text-center text-slate-500">
                                Loading patients...
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </DialogContent>
        </Dialog>
    );
}
