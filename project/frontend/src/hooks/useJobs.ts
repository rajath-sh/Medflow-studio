import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Query Keys ──────────────────────────────────────────
export const jobKeys = {
    all: ["jobs"] as const,
    detail: (id: string) => ["jobs", id] as const,
    logs: (id: string) => ["jobs", id, "logs"] as const,
};

// ── Types ───────────────────────────────────────────────
export interface Job {
    id: string;
    workflow_id: string;
    status: string;
    started_at: string | null;
    completed_at: string | null;
    error: string | null;
    retry_count: number;
}

export interface JobLog {
    id: string;
    level: string;
    message: string;
    timestamp: string;
}

// ── Fetchers ────────────────────────────────────────────

async function fetchJobs(): Promise<Job[]> {
    const res = await api.get("/jobs/");
    return res.data;
}

async function fetchJob(id: string): Promise<Job> {
    const res = await api.get(`/jobs/${id}`);
    return res.data;
}

async function fetchJobLogs(id: string): Promise<JobLog[]> {
    const res = await api.get(`/jobs/${id}/logs`);
    return res.data;
}

// ── Hooks ───────────────────────────────────────────────

export function useJobs() {
    return useQuery({
        queryKey: jobKeys.all,
        queryFn: fetchJobs,
    });
}

export function useJob(id: string) {
    return useQuery({
        queryKey: jobKeys.detail(id),
        queryFn: () => fetchJob(id),
        enabled: !!id,
        refetchInterval: (query) => {
            // Auto-poll running jobs every 3 seconds
            const status = query.state.data?.status;
            return status === "running" || status === "pending" ? 3000 : false;
        },
    });
}

export function useJobLogs(id: string) {
    return useQuery({
        queryKey: jobKeys.logs(id),
        queryFn: () => fetchJobLogs(id),
        enabled: !!id,
        refetchInterval: (query) => {
            // Poll logs while job is active
            return 5000;
        },
    });
}
