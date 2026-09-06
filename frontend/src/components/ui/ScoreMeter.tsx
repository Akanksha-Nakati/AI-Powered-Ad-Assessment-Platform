import type { Criterion } from "../../lib/api/types";
import { band, BAND_STYLE, CRITERION_COPY, formatScore } from "../../lib/scoring";
import { Icon } from "./Icon";

type Props = {
  criterion: Criterion;
  score: number | undefined;
  /** Drop the explanatory blurb where the column is too narrow to carry it. */
  compact?: boolean;
};

/**
 * One criterion. The bar is the magnitude; the chip carries the verdict in
 * words and an icon, so the colour is never the only thing saying "this is bad".
 */
export function ScoreMeter({ criterion, score, compact = false }: Props) {
  const copy = CRITERION_COPY[criterion];
  if (score === undefined) {
    return (
      <div className="space-y-2">
        <p className="text-sm font-medium text-ink">{copy.label}</p>
        <p className="text-sm text-ink-muted">Not scored</p>
      </div>
    );
  }

  const b = band(score);
  const style = BAND_STYLE[b];

  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-sm font-medium text-ink">{copy.label}</p>
        <span className="text-sm tabular-nums text-ink-soft">
          <span className="font-semibold text-ink">{formatScore(score)}</span>
          <span className="text-ink-muted">/10</span>
        </span>
      </div>

      <div
        className="h-2 w-full overflow-hidden rounded-full bg-black/[0.06]"
        role="img"
        aria-label={`${copy.label}: ${formatScore(score)} out of 10, ${style.label}`}
      >
        {/* 4px rounded data-end anchored to the baseline. */}
        <div
          className={`h-full rounded-full transition-[width] duration-700 ease-out ${style.mark}`}
          style={{ width: `${Math.max(2, (score / 10) * 100)}%` }}
        />
      </div>

      <div className="flex items-center gap-1.5">
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${style.chip}`}
        >
          <Icon path={style.icon} className="h-3 w-3" />
          {style.label}
        </span>
        {!compact && (
          <span className="hidden text-xs text-ink-muted lg:inline">{copy.blurb}</span>
        )}
      </div>
    </div>
  );
}
