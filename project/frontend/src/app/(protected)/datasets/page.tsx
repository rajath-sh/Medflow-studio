"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useGeneralDatasets, useUploadGeneralDataset, useDeleteGeneralDataset, Dataset } from "@/hooks/useDatasets";
import { FileUp, Trash2, Cpu, Edit, FileText } from "lucide-react";
import toast from "react-hot-toast";

export default function DatasetsPage() {
    const router = useRouter();
    const { user } = useAuth();
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const { data: datasets, isLoading, isError } = useGeneralDatasets();
    const uploadMutation = useUploadGeneralDataset();
    const deleteMutation = useDeleteGeneralDataset();

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setSelectedFile(e.target.files[0]);
        }
    };

    const handleUpload = () => {
        if (!selectedFile) return;
        uploadMutation.mutate(selectedFile, {
            onSuccess: () => {
                toast.success("Dataset uploaded successfully!");
                setSelectedFile(null);
            },
            onError: (error) => {
                toast.error(`Upload failed: ${error.message}`);
            },
        });
    };

    const handleDelete = (filename: string) => {
        if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
        deleteMutation.mutate(filename, {
            onSuccess: () => toast.success("Dataset deleted"),
            onError: (error) => toast.error(`Delete failed: ${error.message}`),
        });
    };

    const handleDesignManually = (dataset: Dataset) => {
        router.push(`/workflow?source_file=${encodeURIComponent(dataset.path)}`);
    };

    const handleAskAI = (dataset: Dataset) => {
        router.push(`/ai?source_file=${encodeURIComponent(dataset.path)}`);
    };

    if (isLoading) return <div className="p-8">Loading datasets...</div>;
    if (isError) return <div className="p-8 text-red-500">Failed to load datasets</div>;

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-gray-800">General Datasets</h1>
                <div className="text-sm text-gray-500">Manage multi-patient and general datasets</div>
            </div>

            {/* Upload Zone */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
                <h2 className="text-xl font-semibold mb-4 text-gray-800">Upload New Dataset</h2>
                <div className="flex gap-4 items-center">
                    <input
                        type="file"
                        accept=".csv,.txt,.json"
                        onChange={handleFileChange}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    <button
                        onClick={handleUpload}
                        disabled={!selectedFile || uploadMutation.isPending}
                        className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                    >
                        <FileUp size={18} />
                        {uploadMutation.isPending ? "Uploading..." : "Upload"}
                    </button>
                </div>
            </div>

            {/* Dataset List */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-50 border-b border-gray-200 text-gray-700">
                            <th className="p-4 font-semibold">Filename</th>
                            <th className="p-4 font-semibold">Size</th>
                            <th className="p-4 font-semibold">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {!datasets || datasets.length === 0 ? (
                            <tr>
                                <td colSpan={3} className="p-8 text-center text-gray-500">
                                    <FileText size={48} className="mx-auto text-gray-300 mb-2" />
                                    No datasets uploaded yet.
                                </td>
                            </tr>
                        ) : (
                            datasets.map((dataset) => (
                                <tr key={dataset.filename} className="border-b border-gray-100 hover:bg-gray-50">
                                    <td className="p-4 text-gray-800 font-medium">
                                        {dataset.filename}
                                        <div className="text-xs text-gray-400 mt-1">{dataset.path}</div>
                                    </td>
                                    <td className="p-4 text-gray-600">
                                        {(dataset.size / 1024).toFixed(2)} KB
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <button
                                                onClick={() => handleDesignManually(dataset)}
                                                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded border border-indigo-200 transition-colors"
                                                title="Open in Workflow Designer"
                                            >
                                                <Edit size={16} />
                                                Design Manually
                                            </button>
                                            <button
                                                onClick={() => handleAskAI(dataset)}
                                                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-purple-50 text-purple-700 hover:bg-purple-100 rounded border border-purple-200 transition-colors"
                                                title="Generate ETL Pipeline with AI"
                                            >
                                                <Cpu size={16} />
                                                Ask AI to Build
                                            </button>
                                            {(user?.role === "SuperAdmin" || user?.role === "Admin" || user?.role === "Manager") && (
                                                <button
                                                    onClick={() => handleDelete(dataset.filename)}
                                                    className="p-1.5 text-red-500 hover:bg-red-50 rounded transition-colors ml-4"
                                                    title="Delete Dataset"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
