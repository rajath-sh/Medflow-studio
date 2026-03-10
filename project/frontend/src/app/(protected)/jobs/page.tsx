"use client";

import { useState } from "react";
import { useJobs, Job } from "@/hooks/useJobs";
import JobStatusCard from "@/components/JobStatusCard";
import LogViewer from "@/components/LogViewer";
import { api, getAccessToken } from "@/lib/api";

export default function JobsPage() {
    const { data: jobs = [], isLoading, refetch } = useJobs();
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [downloading, setDownloading] = useState(false);

    const downloadResult = async (jobId: string) => {
        setDownloading(true);
        try {
            const token = getAccessToken();
            const response = await api.get(`/jobs/${jobId}/download${token ? `?token=${token}` : ''}`, {
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `project_${jobId}.zip`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Download failed", err);
            alert("Download failed. The file might be missing or status mismatch.");
        } finally {
            setDownloading(false);
        }
    };

    const pendingCount = jobs.filter((j) => j.status?.toLowerCase() === "pending").length;
    const runningCount = jobs.filter((j) => j.status?.toLowerCase() === "running").length;
    const completedCount = jobs.filter((j) => (j.status?.toLowerCase() === "completed" || j.status?.toLowerCase() === "success")).length;
    const failedCount = jobs.filter((j) => j.status?.toLowerCase() === "failed").length;

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Job Dashboard</h1>
                <button
                    onClick={() => refetch()}
                    className="px-4 py-2 bg-gray-100 rounded-lg text-sm hover:bg-gray-200 transition"
                >
                    🔄 Refresh
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg text-center">
                    <p className="text-2xl font-bold text-yellow-600">{pendingCount}</p>
                    <p className="text-xs text-gray-500">Pending</p>
                </div>
                <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg text-center">
                    <p className="text-2xl font-bold text-blue-600">{runningCount}</p>
                    <p className="text-xs text-gray-500">Running</p>
                </div>
                <div className="bg-green-50 border border-green-200 p-4 rounded-lg text-center">
                    <p className="text-2xl font-bold text-green-600">{completedCount}</p>
                    <p className="text-xs text-gray-500">Completed</p>
                </div>
                <div className="bg-red-50 border border-red-200 p-4 rounded-lg text-center">
                    <p className="text-2xl font-bold text-red-600">{failedCount}</p>
                    <p className="text-xs text-gray-500">Failed</p>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-6">
                {/* Job list */}
                <div className="col-span-1 space-y-3">
                    <h2 className="font-semibold text-gray-600 text-sm uppercase tracking-wide">
                        Execution History
                    </h2>

                    {isLoading && <p className="text-sm text-gray-400">Loading jobs...</p>}

                    {!isLoading && jobs.length === 0 && (
                        <div className="text-center text-gray-400 py-8">
                            <p className="text-3xl mb-2">📭</p>
                            <p className="text-sm">No jobs yet</p>
                            <p className="text-xs">Execute a workflow to see jobs here</p>
                        </div>
                    )}

                    {jobs.map((job) => (
                        <JobStatusCard
                            key={job.id}
                            job={job}
                            isSelected={selectedJob?.id === job.id}
                            onSelect={setSelectedJob}
                        />
                    ))}
                </div>

                {/* Detail + logs */}
                <div className="col-span-2">
                    {selectedJob ? (
                        <div className="space-y-4">
                            <div className="bg-white p-4 rounded-lg border">
                                <h2 className="font-semibold mb-3">Job Detail</h2>
                                <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                                    <p><span className="text-gray-500 block mb-0.5">ID</span> <span className="font-mono text-xs">{selectedJob.id}</span></p>
                                    <p><span className="text-gray-500 block mb-0.5">Status</span> <span className="capitalize">{selectedJob.status}</span></p>
                                    <p><span className="text-gray-500 block mb-0.5">Workflow</span> {selectedJob.workflow_id}</p>
                                    <p><span className="text-gray-500 block mb-0.5">Retries</span> {selectedJob.retry_count || 0}</p>
                                    {selectedJob.started_at && (
                                        <p><span className="text-gray-500 block mb-0.5">Started</span> {new Date(selectedJob.started_at).toLocaleString()}</p>
                                    )}
                                    {selectedJob.completed_at && (
                                        <p><span className="text-gray-500 block mb-0.5">Completed</span> {new Date(selectedJob.completed_at).toLocaleString()}</p>
                                    )}
                                </div>

                                {selectedJob.status?.toLowerCase() === "success" && (
                                    <div className="mt-4 pt-4 border-t">
                                        <button
                                            onClick={() => downloadResult(selectedJob.id)}
                                            disabled={downloading}
                                            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition disabled:opacity-50 shadow-sm"
                                        >
                                            {downloading ? "⌛ Preparing..." : "📥 Download Project ZIP"}
                                        </button>
                                        <p className="text-[10px] text-gray-400 mt-2 italic">
                                            Note: Only Project Generation jobs provide a downloadable ZIP.
                                        </p>
                                    </div>
                                )}

                                {selectedJob.error && (
                                    <div className="mt-3 bg-red-50 border border-red-200 p-3 rounded-lg text-xs text-red-700 break-words font-mono">
                                        {selectedJob.error}
                                    </div>
                                )}
                            </div>

                            <div className="bg-white p-4 rounded-lg border">
                                <h2 className="font-semibold mb-3">Execution Logs</h2>
                                <LogViewer jobId={selectedJob.id} />
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-64 text-gray-400 bg-white rounded-xl border border-dashed">
                            <div className="text-center">
                                <p className="text-3xl mb-2">📋</p>
                                <p className="text-sm">Select a job from history to view details</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
