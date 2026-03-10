"use client";

import { useJobLogs, JobLog } from "@/hooks/useJobs";

type Props = {
    jobId: string;
};

const LEVEL_STYLES: Record<string, string> = {
    INFO: "text-blue-600",
    WARNING: "text-yellow-600",
    ERROR: "text-red-600",
    DEBUG: "text-gray-400",
};

export default function LogViewer({ jobId }: Props) {
    const { data: logs = [], isLoading } = useJobLogs(jobId);

    if (isLoading) {
        return <p className="text-sm text-gray-400 p-4">Loading logs...</p>;
    }

    if (logs.length === 0) {
        return <p className="text-sm text-gray-400 p-4">No logs yet.</p>;
    }

    return (
        <div className="bg-gray-900 rounded-lg p-3 max-h-96 overflow-y-auto font-mono text-xs">
            {logs.map((log) => (
                <div key={log.id} className="flex gap-2 py-0.5">
                    <span className="text-gray-500 shrink-0">
                        {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span
                        className={`shrink-0 w-16 text-right ${LEVEL_STYLES[log.level] || "text-gray-300"
                            }`}
                    >
                        [{log.level}]
                    </span>
                    <span className="text-gray-200">{log.message}</span>
                </div>
            ))}
        </div>
    );
}
