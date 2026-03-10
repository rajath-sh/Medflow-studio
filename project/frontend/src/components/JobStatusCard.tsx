"use client";

import { Job } from "@/hooks/useJobs";

type Props = {
    job: Job;
    onSelect: (job: Job) => void;
    isSelected: boolean;
};

const STATUS_STYLES: Record<string, { color: string; bg: string; icon: string }> = {
    pending: { color: "#ca8a04", bg: "#fef9c3", icon: "⏳" },
    running: { color: "#2563eb", bg: "#dbeafe", icon: "🔄" },
    completed: { color: "#16a34a", bg: "#dcfce7", icon: "✅" },
    success: { color: "#16a34a", bg: "#dcfce7", icon: "✅" },
    failed: { color: "#dc2626", bg: "#fee2e2", icon: "❌" },
};

export default function JobStatusCard({ job, onSelect, isSelected }: Props) {
    const style = STATUS_STYLES[job.status?.toLowerCase()] || STATUS_STYLES.pending;

    return (
        <div
            onClick={() => onSelect(job)}
            className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${isSelected ? "ring-2 ring-blue-400" : ""
                }`}
            style={{ borderColor: style.color, backgroundColor: style.bg }}
        >
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold" style={{ color: style.color }}>
                    {style.icon} {job.status.toUpperCase()}
                </span>
                <span className="text-xs text-gray-500 font-mono">
                    {job.id.substring(0, 8)}…
                </span>
            </div>

            <div className="text-xs text-gray-600 space-y-1">
                {job.started_at && (
                    <p>Started: {new Date(job.started_at).toLocaleString()}</p>
                )}
                {job.completed_at && (
                    <p>Completed: {new Date(job.completed_at).toLocaleString()}</p>
                )}
                {job.error && (
                    <p className="text-red-600 truncate">Error: {job.error}</p>
                )}
            </div>
        </div>
    );
}
