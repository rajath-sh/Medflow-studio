import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Dataset {
    filename: string;
    path: string;
    size: number;
}

export const useGeneralDatasets = () => {
    return useQuery({
        queryKey: ["generalDatasets"],
        queryFn: async () => {
            const { data } = await api.get<Dataset[]>("/datasets/general");
            return data;
        },
    });
};

export const useUploadGeneralDataset = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (file: File) => {
            const formData = new FormData();
            formData.append("file", file);
            const { data } = await api.post("/datasets/general", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["generalDatasets"] });
        },
    });
};

export const useDeleteGeneralDataset = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (filename: string) => {
            await api.delete(`/datasets/general/${filename}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["generalDatasets"] });
        },
    });
};

export const usePatientDatasets = (patientId: string) => {
    return useQuery({
        queryKey: ["patientDatasets", patientId],
        queryFn: async () => {
            const { data } = await api.get<Dataset[]>(`/patients/${patientId}/datasets`);
            return data;
        },
        enabled: !!patientId,
    });
};

export const useUploadPatientDataset = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ patientId, file }: { patientId: string; file: File }) => {
            const formData = new FormData();
            formData.append("file", file);
            const { data } = await api.post(`/patients/${patientId}/datasets`, formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            return data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["patientDatasets", variables.patientId] });
        },
    });
};

export const useDeletePatientDataset = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ patientId, filename }: { patientId: string; filename: string }) => {
            await api.delete(`/patients/${patientId}/datasets/${filename}`);
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["patientDatasets", variables.patientId] });
        },
    });
};
