import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { EmptyState, ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { ScoreBar } from "../../components/ui/ScoreBar";
import { ApiError, api } from "../../lib/api/client";
import { CRITERIA } from "../../lib/api/types";
import { queryKeys } from "../../lib/query";
import { DEFAULT_PLACEMENT, PlacementFields, type Placement } from "../assess/PlacementFields";

const MIN_VARIANTS = 2;
const MAX_VARIANTS = 5;

export function ComparePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [placement, setPlacement] = useState<Placement>(DEFAULT_PLACEMENT);

  const brands = useQuery({ queryKey: queryKeys.brands, queryFn: api.listBrands });

  const compare = useMutation({
    mutationFn: () =>
      api.compare({
        images: files,
        platform: placement.platform,
        industry: placement.industry,
        adType: placement.adType,
        brandId: placement.brandId || null,
      }),
  });

  const countOk = files.length >= MIN_VARIANTS && files.length <= MAX_VARIANTS;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <section className="lg:col-span-1 card glass p-5">
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            compare.mutate();
          }}
        >
          <div>
            <span className="text-sm text-slate-200">
              Variants{" "}
              <span className="text-slate-500">
                ({MIN_VARIANTS}&ndash;{MAX_VARIANTS})
              </span>
            </span>
            <div className="mt-2 rounded-2xl border border-dashed border-cyan-500/50 bg-cyan-500/5 p-4">
              <input
                type="file"
                multiple
                accept="image/png,image/jpeg,image/webp,image/gif"
                onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
                className="text-sm text-slate-200"
              />
              {files.length > 0 && (
                <ul className="mt-3 space-y-1 text-xs text-slate-300">
                  {files.map((f) => (
                    <li key={f.name}>{f.name}</li>
                  ))}
                </ul>
              )}
            </div>
            {files.length > 0 && !countOk && (
              <p className="mt-2 text-xs text-amber-300">
                Choose between {MIN_VARIANTS} and {MAX_VARIANTS} variants.
              </p>
            )}
          </div>

          <PlacementFields
            value={placement}
            onChange={setPlacement}
            brands={brands.data ?? []}
          />

          <button
            type="submit"
            disabled={compare.isPending || !countOk}
            className="w-full rounded-xl bg-gradient-to-r from-cyan-500 via-blue-500 to-violet-600 px-4 py-3 font-semibold shadow-lg shadow-cyan-500/20 transition hover:opacity-90 disabled:opacity-50"
          >
            {compare.isPending ? "Comparing..." : "Compare Variants"}
          </button>
          {compare.isError && (
            <ErrorMessage title="Comparison failed">
              {compare.error instanceof ApiError
                ? compare.error.message
                : String(compare.error)}
            </ErrorMessage>
          )}
        </form>
      </section>

      <section className="lg:col-span-2 space-y-4">
        {compare.isPending && (
          <div className="card glass p-6">
            <Spinner label={`Scoring ${files.length} variants...`} />
          </div>
        )}
        {!compare.isPending && !compare.data && (
          <EmptyState title="No comparison yet">
            Upload several versions of the same ad to see which one scores best and why.
          </EmptyState>
        )}
        {compare.data && (
          <div className="space-y-4">
            {compare.data.entries.map((entry) => (
              <div key={entry.assessment.id} className="card glass p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className={
                        entry.rank === 1
                          ? "rounded-full bg-cyan-400/20 px-3 py-1 text-sm font-semibold text-cyan-200"
                          : "rounded-full bg-white/5 px-3 py-1 text-sm text-slate-300"
                      }
                    >
                      #{entry.rank}
                    </span>
                    <span className="font-medium text-white">{entry.label}</span>
                    {entry.rank === 1 && (
                      <span className="text-xs uppercase tracking-wide text-cyan-300">
                        Winner
                      </span>
                    )}
                  </div>
                  <span className="text-2xl font-bold text-white">
                    {entry.assessment.scorecard.overall_score.toFixed(1)}
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  {CRITERIA.map((c) => (
                    <ScoreBar
                      key={c}
                      label={c}
                      value={entry.assessment.scorecard.scores[c]}
                    />
                  ))}
                </div>

                <p className="text-sm text-slate-300">
                  {entry.assessment.scorecard.feedback}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
