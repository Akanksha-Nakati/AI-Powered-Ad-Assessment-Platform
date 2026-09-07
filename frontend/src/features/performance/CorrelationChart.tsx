import { EmptyState } from "../../components/ui/Feedback";
import { icons } from "../../components/ui/Icon";
import type { CorrelationResult } from "../../lib/api/types";
import { formatScore } from "../../lib/scoring";

type Props = { result: CorrelationResult };

const WIDTH = 480;
const HEIGHT = 260;
const PAD = { top: 16, right: 16, bottom: 32, left: 44 };

/** Plain-language read of the coefficient -- the number alone answers "is
 * there a relationship", but not "how should I feel about that". */
function describe(r: number): string {
  const strength =
    Math.abs(r) >= 0.7 ? "a strong" : Math.abs(r) >= 0.4 ? "a moderate" : "a weak";
  const direction = r >= 0 ? "positive" : "negative";
  return `${strength} ${direction} relationship`;
}

export function CorrelationChart({ result }: Props) {
  const { points, pearson_r, matched_count, unmatched_assessments, unmatched_metrics } =
    result;

  if (matched_count === 0) {
    return (
      <EmptyState title="Nothing to compare yet" icon={icons.target}>
        Tag a checked ad with its identifier in your warehouse, then refresh this
        connection, and it'll show up here next to how it actually performed.
      </EmptyState>
    );
  }

  const plottable = points.filter(
    (p): p is typeof p & { avg_ctr: number } => p.avg_ctr !== null,
  );

  return (
    <div className="card p-6">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-base font-semibold text-ink">Score vs. real performance</h2>
        <span className="text-sm text-ink-soft">
          {matched_count} matched ad{matched_count === 1 ? "" : "s"}
        </span>
      </div>

      <p className="mt-1 text-sm text-ink-soft">
        {pearson_r === null
          ? "Not enough matched data yet to tell whether these scores predict performance."
          : `Across these ads, higher scores tend to track with ${describe(pearson_r)} in click-through rate (r = ${pearson_r.toFixed(2)}).`}
      </p>

      {plottable.length > 0 && <Scatter points={plottable} />}

      {(unmatched_assessments > 0 || unmatched_metrics > 0) && (
        <p className="mt-4 text-xs text-ink-muted">
          {unmatched_assessments > 0 &&
            `${unmatched_assessments} tagged check${unmatched_assessments === 1 ? "" : "s"} not in this data. `}
          {unmatched_metrics > 0 &&
            `${unmatched_metrics} row${unmatched_metrics === 1 ? "" : "s"} in your warehouse aren't tagged on any check yet.`}
        </p>
      )}

      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs text-ink-muted">
              <th className="pb-2 font-medium">Ad</th>
              <th className="pb-2 font-medium">Score</th>
              <th className="pb-2 font-medium">CTR</th>
              <th className="pb-2 font-medium">Spend</th>
              <th className="pb-2 font-medium">Conversions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {points.map((p) => (
              <tr key={p.assessment_id}>
                <td className="py-2 pr-3 font-mono text-xs text-ink-soft">
                  {p.external_ad_id}
                </td>
                <td className="py-2 pr-3 font-medium text-ink">
                  {formatScore(p.overall_score)}
                </td>
                <td className="py-2 pr-3 text-ink-soft">
                  {p.avg_ctr === null ? "—" : `${(p.avg_ctr * 100).toFixed(2)}%`}
                </td>
                <td className="py-2 pr-3 text-ink-soft">
                  {p.total_spend === null ? "—" : `$${p.total_spend.toFixed(0)}`}
                </td>
                <td className="py-2 text-ink-soft">{p.total_conversions ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Scatter({ points }: { points: { overall_score: number; avg_ctr: number }[] }) {
  const maxCtr = Math.max(...points.map((p) => p.avg_ctr));
  const yMax = maxCtr > 0 ? maxCtr * 1.15 : 1;

  const x = (score: number) =>
    PAD.left + (score / 10) * (WIDTH - PAD.left - PAD.right);
  const y = (ctr: number) =>
    HEIGHT - PAD.bottom - (ctr / yMax) * (HEIGHT - PAD.top - PAD.bottom);

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="mt-4 w-full"
      role="img"
      aria-label="Scatter plot of creative score against click-through rate"
    >
      <line
        x1={PAD.left}
        y1={HEIGHT - PAD.bottom}
        x2={WIDTH - PAD.right}
        y2={HEIGHT - PAD.bottom}
        stroke="#e6e5e0"
      />
      <line
        x1={PAD.left}
        y1={PAD.top}
        x2={PAD.left}
        y2={HEIGHT - PAD.bottom}
        stroke="#e6e5e0"
      />

      {[0, 5, 10].map((tick) => (
        <text
          key={tick}
          x={x(tick)}
          y={HEIGHT - PAD.bottom + 18}
          textAnchor="middle"
          className="fill-ink-muted text-[10px]"
        >
          {tick}
        </text>
      ))}
      <text
        x={WIDTH / 2}
        y={HEIGHT - 2}
        textAnchor="middle"
        className="fill-ink-muted text-[10px]"
      >
        Score
      </text>
      <text
        x={-HEIGHT / 2}
        y={12}
        textAnchor="middle"
        transform="rotate(-90)"
        className="fill-ink-muted text-[10px]"
      >
        CTR
      </text>

      {points.map((p, i) => (
        <circle
          key={i}
          cx={x(p.overall_score)}
          cy={y(p.avg_ctr)}
          r={5}
          className="fill-brand-600/70"
        >
          <title>
            {formatScore(p.overall_score)}/10, {(p.avg_ctr * 100).toFixed(2)}% CTR
          </title>
        </circle>
      ))}
    </svg>
  );
}
