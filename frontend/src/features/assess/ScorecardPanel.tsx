import { CitationList } from "../../components/ui/CitationList";
import { ScoreBar } from "../../components/ui/ScoreBar";
import { ScoreDial } from "../../components/ui/ScoreDial";
import type { Assessment } from "../../lib/api/types";
import { CRITERIA } from "../../lib/api/types";

export function ScorecardPanel({ assessment }: { assessment: Assessment }) {
  const { scorecard, visual_analysis, context } = assessment;

  return (
    <div className="space-y-4">
      <div className="card glass p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-300">Overall score</p>
            <h2 className="text-3xl font-bold text-white">
              {scorecard.overall_score.toFixed(1)}/10
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              {assessment.metadata.platform} &middot; {assessment.metadata.industry}{" "}
              &middot; {assessment.metadata.ad_type}
            </p>
          </div>
          <ScoreDial score={scorecard.overall_score} />
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {CRITERIA.map((key) => (
            <ScoreBar key={key} label={key} value={scorecard.scores[key]} />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card glass p-5 space-y-3">
          <h3 className="text-lg font-semibold text-white">Feedback</h3>
          <p className="text-sm text-slate-200">{scorecard.feedback}</p>
        </div>
        <div className="card glass p-5 space-y-3">
          <h3 className="text-lg font-semibold text-white">Recommendations</h3>
          <ul className="space-y-2 text-sm text-slate-200">
            {scorecard.recommendations.map((rec, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-cyan-300">&bull;</span>
                <span>{rec}</span>
              </li>
            ))}
            {scorecard.recommendations.length === 0 && (
              <li className="text-slate-400">No recommendations returned.</li>
            )}
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card glass p-5 space-y-3">
          <h3 className="text-lg font-semibold text-white">What the model saw</h3>
          <dl className="space-y-2 text-sm text-slate-200">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400">Copy</dt>
              <dd>{visual_analysis.text || "-"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400">Layout</dt>
              <dd>{visual_analysis.layout || "-"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400">CTA</dt>
              <dd>{visual_analysis.cta || "None detected"}</dd>
            </div>
            {visual_analysis.colors.length > 0 && (
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-400">Colors</dt>
                <dd className="mt-1 flex flex-wrap gap-2">
                  {visual_analysis.colors.map((c) => (
                    <span
                      key={c}
                      className="rounded-full border border-white/10 px-2 py-0.5 text-xs"
                    >
                      {c}
                    </span>
                  ))}
                </dd>
              </div>
            )}
          </dl>
        </div>
        <CitationList citations={scorecard.citations} context={context} />
      </div>
    </div>
  );
}
