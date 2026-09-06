import { useState } from "react";
import { Icon, icons } from "../../components/ui/Icon";
import { ScoreMeter } from "../../components/ui/ScoreMeter";
import { ScoreRing } from "../../components/ui/ScoreRing";
import type { Assessment } from "../../lib/api/types";
import { CRITERIA } from "../../lib/api/types";
import { band, overallVerdict, sourceLabel } from "../../lib/scoring";

const BAND_BORDER = {
  strong: "border-score-strong/25 bg-score-strong/[0.04]",
  mid: "border-score-mid/30 bg-score-mid/[0.06]",
  weak: "border-score-weak/25 bg-score-weak/[0.04]",
} as const;

export function ScorecardPanel({ assessment }: { assessment: Assessment }) {
  const { scorecard, context, metadata } = assessment;
  const overall = scorecard.overall_score;
  const weakest = [...CRITERIA]
    .filter((c) => scorecard.scores[c] !== undefined)
    .sort((a, b) => (scorecard.scores[a] ?? 0) - (scorecard.scores[b] ?? 0))[0];

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Headline */}
      <section className="card overflow-hidden">
        <div className="flex flex-col items-center gap-6 p-6 sm:flex-row sm:items-center">
          <ScoreRing score={overall} />
          <div className="min-w-0 flex-1 text-center sm:text-left">
            <p className="text-sm text-ink-muted">Overall</p>
            <h2 className="mt-0.5 text-2xl font-semibold tracking-tight text-ink">
              {overallVerdict(overall)}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">
              {scorecard.feedback}
            </p>
            <p className="mt-3 text-xs text-ink-muted">
              {metadata.platform} &middot; {metadata.industry} &middot; {metadata.ad_type}
            </p>
          </div>
        </div>

        {weakest && (
          <div className={`border-t border-line px-6 py-4 ${BAND_BORDER[band(scorecard.scores[weakest] ?? 0)]}`}>
            <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
              Weakest area
            </p>
            <p className="mt-1 text-sm font-medium text-ink">
              {scorecard.recommendations[0] ?? "Review the scores below."}
            </p>
          </div>
        )}
      </section>

      {/* Scores */}
      <section className="card p-6">
        <h3 className="text-base font-semibold text-ink">How it scored</h3>
        <div className="mt-6 grid gap-x-10 gap-y-6 sm:grid-cols-2">
          {CRITERIA.map((c) => (
            <ScoreMeter key={c} criterion={c} score={scorecard.scores[c]} />
          ))}
        </div>
      </section>

      {/* Fixes */}
      {scorecard.recommendations.length > 0 && (
        <section className="card p-6">
          <h3 className="text-base font-semibold text-ink">What to change</h3>
          <ol className="mt-4 space-y-3">
            {scorecard.recommendations.map((rec, i) => (
              <li key={i} className="flex gap-3">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
                  {i + 1}
                </span>
                <p className="text-sm leading-relaxed text-ink">{rec}</p>
              </li>
            ))}
          </ol>
        </section>
      )}

      {context.length > 0 && <Basis assessment={assessment} />}
    </div>
  );
}

/**
 * The guidance behind the verdict, collapsed by default.
 *
 * Users want the answer, not the machinery — but "why should I believe this?"
 * is a fair question, so the evidence stays one click away rather than absent.
 */
function Basis({ assessment }: { assessment: Assessment }) {
  const [open, setOpen] = useState(false);
  const { context } = assessment;
  const brandCount = context.filter((c) => c.brand_id).length;

  return (
    <section className="card overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 p-6 text-left transition hover:bg-canvas"
      >
        <div>
          <h3 className="text-base font-semibold text-ink">What this is based on</h3>
          <p className="mt-0.5 text-sm text-ink-soft">
            {context.length} marketing {context.length === 1 ? "guideline" : "guidelines"}
            {brandCount > 0 && `, including ${brandCount} of your own brand rules`}
          </p>
        </div>
        <Icon
          path={icons.chevronDown}
          className={`h-5 w-5 shrink-0 text-ink-muted transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="space-y-3 border-t border-line bg-canvas p-6">
          {context.map((chunk, i) => (
            <article
              key={`${chunk.source}-${chunk.chunk ?? i}`}
              className="rounded-xl border border-line bg-white p-4"
            >
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium capitalize text-ink">
                  {sourceLabel(chunk)}
                </p>
                {chunk.brand_id && (
                  <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                    Your brand
                  </span>
                )}
              </div>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-ink-soft">
                {chunk.text}
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
