import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Patient } from "@/lib/types";

// ── Query Keys ──────────────────────────────────────────
export const patientKeys = {
    all: ["patients"] as const,
    detail: (id: string) => ["patients", id] as const,
};

// ── Fetchers ────────────────────────────────────────────

async function fetchPatients(): Promise<Patient[]> {
    const res = await api.get("/patients/");
    return res.data;
}

async function fetchPatient(id: string): Promise<Patient> {
    const res = await api.get(`/patients/${id}`);
    return res.data;
}

// ── Hooks ───────────────────────────────────────────────

export function usePatients() {
    return useQuery({
        queryKey: patientKeys.all,
        queryFn: fetchPatients,
    });
}

export function usePatient(id: string) {
    return useQuery({
        queryKey: patientKeys.detail(id),
        queryFn: () => fetchPatient(id),
        enabled: !!id,
    });
}

export function useCreatePatient() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (patient: Omit<Patient, "patient_id">) => {
            const res = await api.post("/patients/", patient);
            return res.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: patientKeys.all });
        },
    });
}

export function useUpdatePatient() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, patient }: { id: string; patient: Omit<Patient, "patient_id"> }) => {
            const res = await api.put(`/patients/${id}`, patient);
            return res.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: patientKeys.all });
        },
    });
}

export function useDeletePatient() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (id: string) => {
            await api.delete(`/patients/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: patientKeys.all });
        },
    });
}
