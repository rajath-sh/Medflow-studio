"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useState } from "react";

/**
 * Wraps the app in TanStack Query's QueryClientProvider.
 * 
 * WHY useState for queryClient?
 * In Next.js App Router, components can re-render on navigation.
 * Using useState ensures we create the QueryClient once and reuse it,
 * preventing cache loss across page transitions.
 */
export default function QueryProvider({ children }: { children: ReactNode }) {
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 30 * 1000, // Data is fresh for 30s
                        retry: 1,             // Retry failed requests once
                        refetchOnWindowFocus: false, // Don't refetch when tab regains focus
                    },
                },
            })
    );

    return (
        <QueryClientProvider client={queryClient}>
            {children}
        </QueryClientProvider>
    );
}
