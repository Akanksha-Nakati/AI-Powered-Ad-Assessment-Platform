import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Assessments can now be tagged with an external_ad_id after creation
      // (see PATCH /assessments/:id), so they're no longer strictly immutable
      // -- but that's a rare, user-initiated edit, not something changing in
      // the background, so a minute of staleness is still a fine default.
      // Tagging invalidates its own query key directly rather than relying on
      // this window to pass.
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
