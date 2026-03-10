import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Workflow } from "@/lib/workflowSchema";

// ── Query Keys ──────────────────────────────────────────
// Centralized keys prevent cache invalidation bugs.
export const workflowKeys = {
    all: ["workflows"] as const,
    detail: (id: string) => ["workflows", id] as const,
};

// ── Fetchers ────────────────────────────────────────────

async function fetchWorkflows(): Promise<Workflow[]> {
    const res = await api.get("/workflows/");
    return res.data;
}

async function fetchWorkflow(id: string): Promise<Workflow> {
    const res = await api.get(`/workflows/${id}`);
    return res.data;
}

// ── Hooks ───────────────────────────────────────────────

export function useWorkflows() {
    return useQuery({
        queryKey: workflowKeys.all,
        queryFn: fetchWorkflows,
    });
}

export function useWorkflow(id: string) {
    return useQuery({
        queryKey: workflowKeys.detail(id),
        queryFn: () => fetchWorkflow(id),
        enabled: !!id,
    });
}

export function useSaveWorkflow() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (workflow: { name: string; definition: Workflow }) => {
            const res = await api.post("/workflows/", workflow);
            return res.data;
        },
        onSuccess: () => {
            // Invalidate and refetch the workflows list
            queryClient.invalidateQueries({ queryKey: workflowKeys.all });
        },
    });
}

export function useDeleteWorkflow() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (id: string) => {
            await api.delete(`/workflows/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: workflowKeys.all });
        },
    });
}
