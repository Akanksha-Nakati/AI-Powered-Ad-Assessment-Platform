import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AnalysingCard, EmptyState, ErrorMessage } from "../../components/ui/Feedback";
import { Icon, icons } from "../../components/ui/Icon";
import { ScoreMeter } from "../../components/ui/ScoreMeter";
import { UploadZone } from "../../components/ui/UploadZone";
import { ApiError, api } from "../../lib/api/client";
import { CRITERIA } from "../../lib/api/types";
import { queryKeys } from "../../lib/query";
import { formatScore, overallVerdict } from "../../lib/scoring";
import {
  DEFAULT_PLACEMENT,
  PlacementFields,
  type Placement,
} from "../assess/PlacementFields";

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
    <div className="grid gap-6 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
      <section>
        <div className="card p-6">
          <h1 className="text-lg font-semibold text-ink">Compare versions</h1>
          <p className="mt-1 text-sm text-ink-soft">
            Upload two to five versions of the same ad and see which one to run.
          </p>

          <form
            className="mt-6 space-y-5"
            onSubmit={(e) => {
              e.preventDefault();
              if (countOk) compare.mutate();
            }}
          >
            <UploadZone
              files={files}
              onChange={setFiles}
              multiple
              maxFiles={MAX_VARIANTS}
              hint={`${MIN_VARIANTS}–${MAX_VARIANTS} versions`}
            />

            {files.length > 0 && !countOk && (
              <p className="text-sm text-score-mid-ink">
                Add {files.length < MIN_VARIANTS ? "at least one more version" : "fewer versions"} to compare.
              </p>
            )}

            <PlacementFields
              value={placement}
              onChange={setPlacement}
              brands={brands.data ?? []}
            />

            <button
              type="submit"
              disabled={compare.isPending || !countOk}
              className="btn-primary w-full py-3"
            >
              {compare.isPending ? "Comparing…" : "Compare versions"}
              {!compare.isPending && <Icon path={icons.arrowRight} className="h-4 w-4" />}
            </button>

            {compare.isError && (
              <ErrorMessage title="We couldn't compare those">
                {compare.error instanceof ApiError
                  ? compare.error.message
                  : "Something went wrong. Please try again."}
              </ErrorMessage>
            )}
          </form>
        </div>
      </section>

      <section className="space-y-4">
        {compare.isPending && (
          <AnalysingCard note={`Scoring ${files.length} versions…`} />
        )}

        {!compare.isPending && !compare.data && (
          <EmptyState title="Pick a winner with confidence" icon={icons.layers}>
            Upload a few versions of the same ad. We'll score each one and rank them,
            so you know which to put money behind.
          </EmptyState>
        )}

        {!compare.isPending &&
          compare.data?.entries.map((entry) => {
            const sc = entry.assessment.scorecard;
            const isWinner = entry.rank === 1;
            return (
              <article
                key={entry.assessment.id}
                className={
                  "card animate-fade-up overflow-hidden " +
                  (isWinner ? "ring-2 ring-brand-600" : "")
                }
              >
                {isWinner && (
                  <div className="flex items-center gap-2 bg-brand-600 px-6 py-2 text-sm font-semibold text-white">
                    <Icon path={icons.check} className="h-4 w-4" />
                    Run this one
                  </div>
                )}
                <div className="flex flex-wrap items-center justify-between gap-4 p-6">
                  <div className="min-w-0">
                    <p className="text-xs text-ink-muted">#{entry.rank}</p>
                    <p className="truncate text-base font-semibold text-ink">
                      {entry.label}
                    </p>
                    <p className="mt-0.5 text-sm text-ink-soft">
                      {overallVerdict(sc.overall_score)}
                    </p>
                  </div>
                  <p className="text-3xl font-semibold tabular-nums tracking-tight text-ink">
                    {formatScore(sc.overall_score)}
                    <span className="text-base font-normal text-ink-muted">/10</span>
                  </p>
                </div>

                <div className="grid gap-x-10 gap-y-5 border-t border-line p-6 sm:grid-cols-2">
                  {CRITERIA.map((c) => (
                    <ScoreMeter key={c} criterion={c} score={sc.scores[c]} compact />
                  ))}
                </div>

                <p className="border-t border-line bg-canvas p-6 text-sm leading-relaxed text-ink-soft">
                  {sc.feedback}
                </p>
              </article>
            );
          })}
      </section>
    </div>
  );
}
