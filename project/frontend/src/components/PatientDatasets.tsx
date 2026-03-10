"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
    usePatientDatasets,
    useUploadPatientDataset,
    useDeletePatientDataset,
    Dataset,
} from "@/hooks/useDatasets";
import { FileUp, Trash2, Cpu, Edit, FileText } from "lucide-react";
import toast from "react-hot-toast";

export default function PatientDatasets({ patientId }: { patientId: string }) {
    const router = useRouter();
    const { user } = useAuth();
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const { data: datasets, isLoading, isError } = usePatientDatasets(patientId);
    const uploadMutation = useUploadPatientDataset();
    const deleteMutation = useDeletePatientDataset();

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setSelectedFile(e.target.files[0]);
        }
    };

    const handleUpload = () => {
        if (!selectedFile) return;
        uploadMutation.mutate(
            { patientId, file: selectedFile },
            {
                onSuccess: () => {
                    toast.success("Patient dataset uploaded!");
                    setSelectedFile(null);
                },
                onError: (error) => toast.error(`Upload failed: ${error.message}`),
            }
        );
    };

    const handleDelete = (filename: string) => {
        if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
        deleteMutation.mutate(
            { patientId, filename },
            {
                onSuccess: () => toast.success("Dataset deleted"),
                onError: (error) => toast.error(`Delete failed: ${error.message}`),
            }
        );
    };

    const handleDesignManually = (dataset: Dataset) => {
        router.push(`/workflow?source_file=${encodeURIComponent(dataset.path)}`);
    };

    const handleAskAI = (dataset: Dataset) => {
        router.push(`/ai?source_file=${encodeURIComponent(dataset.path)}`);
    };

    if (isLoading) return <div className="p-4 text-gray-500">Loading datasets...</div>;
    if (isError) return <div className="p-4 text-red-500">Failed to load datasets</div>;

    return (
        <div className="bg-slate-50 p-4 border-t border-b border-gray-200 shadow-inner">
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-700 flex items-center gap-2">
                    <FileText size={18} />
                    Patient Datasets
                </h3>

                {/* Upload Zone */}
                <div className="flex gap-2 items-center">
                    <input
                        type="file"
                        accept=".csv,.txt,.json"
                        onChange={handleFileChange}
                        className="block w-full text-xs text-slate-500 file:mr-2 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-blue-100 file:text-blue-700 hover:file:bg-blue-200"
                    />
                    <button
                        onClick={handleUpload}
                        disabled={!selectedFile || uploadMutation.isPending}
                        className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1 text-xs rounded hover:bg-blue-700 disabled:opacity-50"
                    >
                        <FileUp size={14} />
                        {uploadMutation.isPending ? "..." : "Upload"}
                    </button>
                </div>
            </div>

            {/* Dataset List */}
            {(!datasets || datasets.length === 0) ? (
                <div className="text-sm text-gray-500 italic bg-white p-3 rounded border border-gray-200">
                    No datasets attached to this patient yet.
                </div>
            ) : (
                <div className="bg-white rounded border border-gray-200 overflow-hidden">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="bg-slate-100 text-slate-600 border-b border-gray-200">
                                <th className="px-4 py-2 font-medium">Filename</th>
                                <th className="px-4 py-2 font-medium">Size</th>
                                <th className="px-4 py-2 font-medium text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {datasets.map((ds) => (
                                <tr key={ds.filename} className="border-b border-gray-100 last:border-0 hover:bg-slate-50">
                                    <td className="px-4 py-3 font-medium text-slate-800">{ds.filename}</td>
                                    <td className="px-4 py-3 text-slate-500">{(ds.size / 1024).toFixed(2)} KB</td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <button
                                                onClick={() => handleDesignManually(ds)}
                                                className="flex items-center gap-1 px-2 py-1 text-xs bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded border border-indigo-200 transition-colors"
                                                title="Open in Workflow Designer"
                                            >
                                                <Edit size={14} />
                                                Design Manually
                                            </button>
                                            <button
                                                onClick={() => handleAskAI(ds)}
                                                className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-50 text-purple-700 hover:bg-purple-100 rounded border border-purple-200 transition-colors"
                                                title="Generate ETL Pipeline with AI"
                                            >
                                                <Cpu size={14} />
                                                Ask AI to Build
                                            </button>
                                            <button
                                                onClick={() => handleDelete(ds.filename)}
                                                className="p-1 text-red-500 hover:bg-red-50 rounded ml-2"
                                                title="Delete Dataset"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
