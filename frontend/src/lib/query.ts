import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Assessments are immutable once created, so refetching them on every
      // window focus is pure waste.
      staleTime: 60_000,
      retry: 1,
    },
  },
});

export const queryKeys = {
  health: ["health"] as const,
  assessments: ["assessments"] as const,
  assessment: (id: string) => ["assessments", id] as const,
  brands: ["brands"] as const,
  documents: (brandId: string) => ["brands", brandId, "documents"] as const,
};
