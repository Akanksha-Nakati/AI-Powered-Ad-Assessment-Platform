import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ErrorMessage, EmptyState, Spinner } from "../../components/ui/Feedback";
import { ApiError, api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";
import { ImagePicker } from "./ImagePicker";
import { DEFAULT_PLACEMENT, PlacementFields, type Placement } from "./PlacementFields";
import { ScorecardPanel } from "./ScorecardPanel";

export function AssessPage() {
  const [file, setFile] = useState<File | null>(null);
  const [placement, setPlacement] = useState<Placement>(DEFAULT_PLACEMENT);
  const queryClient = useQueryClient();

  const brands = useQuery({ queryKey: queryKeys.brands, queryFn: api.listBrands });

  const assess = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("Please choose an ad image.");
      return api.assess({
        image: file,
        platform: placement.platform,
        industry: placement.industry,
        adType: placement.adType,
        brandId: placement.brandId || null,
      });
    },
    onSuccess: () => {
      // The new assessment belongs in history too.
      queryClient.invalidateQueries({ queryKey: queryKeys.assessments });
    },
  });

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <section className="lg:col-span-1 card p-5 glass">
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            assess.mutate();
          }}
        >
          <ImagePicker file={file} onChange={setFile} />
          <PlacementFields
            value={placement}
            onChange={setPlacement}
            brands={brands.data ?? []}
          />
          <button
            type="submit"
            disabled={assess.isPending || !file}
            className="w-full rounded-xl bg-gradient-to-r from-cyan-500 via-blue-500 to-violet-600 px-4 py-3 font-semibold shadow-lg shadow-cyan-500/20 transition hover:opacity-90 disabled:opacity-50"
          >
            {assess.isPending ? "Analyzing..." : "Assess Ad"}
          </button>
          {assess.isError && (
            <ErrorMessage title="Assessment failed">
              {assess.error instanceof ApiError
                ? assess.error.message
                : (assess.error as Error).message}
            </ErrorMessage>
          )}
        </form>
      </section>

      <section className="lg:col-span-2 space-y-4">
        {assess.isPending && (
          <div className="card glass p-6">
            <Spinner label="Reading the creative and retrieving guidance..." />
          </div>
        )}
        {!assess.isPending && !assess.data && (
          <EmptyState title="No assessment yet">
            Upload an ad to see creative scores, feedback, and citations from the
            marketing knowledge base.
          </EmptyState>
        )}
        {assess.data && <ScorecardPanel assessment={assess.data} />}
      </section>
    </div>
  );
}
