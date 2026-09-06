import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { AnalysingCard, EmptyState, ErrorMessage } from "../../components/ui/Feedback";
import { Icon, icons } from "../../components/ui/Icon";
import { UploadZone } from "../../components/ui/UploadZone";
import { ApiError, api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";
import { DEFAULT_PLACEMENT, PlacementFields, type Placement } from "./PlacementFields";
import { ScorecardPanel } from "./ScorecardPanel";

export function AssessPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [placement, setPlacement] = useState<Placement>(DEFAULT_PLACEMENT);
  const queryClient = useQueryClient();

  const brands = useQuery({ queryKey: queryKeys.brands, queryFn: api.listBrands });

  const assess = useMutation({
    mutationFn: () =>
      api.assess({
        image: files[0],
        platform: placement.platform,
        industry: placement.industry,
        adType: placement.adType,
        brandId: placement.brandId || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.assessments });
    },
  });

  const ready = files.length > 0;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
      {/* Input */}
      <section>
        <div className="card p-6">
          <h1 className="text-lg font-semibold text-ink">Check an ad</h1>
          <p className="mt-1 text-sm text-ink-soft">
            Upload your creative and we'll tell you what's working and what isn't.
          </p>

          <form
            className="mt-6 space-y-5"
            onSubmit={(e) => {
              e.preventDefault();
              if (ready) assess.mutate();
            }}
          >
            <UploadZone files={files} onChange={setFiles} />

            <PlacementFields
              value={placement}
              onChange={setPlacement}
              brands={brands.data ?? []}
            />

            <button
              type="submit"
              disabled={assess.isPending || !ready}
              className="btn-primary w-full py-3"
            >
              {assess.isPending ? "Checking…" : "Check this ad"}
              {!assess.isPending && <Icon path={icons.arrowRight} className="h-4 w-4" />}
            </button>

            {assess.isError && (
              <ErrorMessage title="We couldn't check that ad">
                {assess.error instanceof ApiError
                  ? assess.error.message
                  : "Something went wrong. Please try again."}
              </ErrorMessage>
            )}
          </form>
        </div>

        {brands.data?.length === 0 && (
          <div className="card mt-4 p-5">
            <p className="text-sm font-medium text-ink">Have brand guidelines?</p>
            <p className="mt-1 text-sm text-ink-soft">
              Add them once and every check will flag anything off-brand.
            </p>
            <Link
              to="/app/brands"
              className="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700 hover:text-brand-800"
            >
              Add brand rules
              <Icon path={icons.arrowRight} className="h-3.5 w-3.5" />
            </Link>
          </div>
        )}
      </section>

      {/* Result */}
      <section>
        {assess.isPending && (
          <AnalysingCard note="Reading your creative and checking it against best practice…" />
        )}
        {!assess.isPending && !assess.data && (
          <EmptyState title="Your results will appear here" icon={icons.image}>
            Upload an ad on the left and we'll score it across six things that decide
            whether a creative performs.
          </EmptyState>
        )}
        {!assess.isPending && assess.data && <ScorecardPanel assessment={assess.data} />}
      </section>
    </div>
  );
}
