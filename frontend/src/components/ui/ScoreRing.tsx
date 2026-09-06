import { band, BAND_STYLE, formatScore } from "../../lib/scoring";

const BAND_STROKE: Record<string, string> = {
  strong: "#0ca30c",
  mid: "#fab219",
  weak: "#d03b3b",
};

type Props = { score: number; size?: number; label?: string };

/**
 * The hero number. A ring rather than a bar because this is one headline value,
 * not a comparison -- and the numeral, not the arc, is what gets read.
 */
export function ScoreRing({ score, size = 132, label }: Props) {
  const pct = Math.max(0, Math.min(100, (score / 10) * 100));
  const b = band(score);
  const style = BAND_STYLE[b];

  return (
    <div
      className="relative shrink-0"
      style={{ height: size, width: size }}
      role="img"
      aria-label={`${formatScore(score)} out of 10 — ${style.label}`}
    >
      <svg viewBox="0 0 36 36" className="h-full w-full -rotate-90">
        <circle cx="18" cy="18" r="15.9155" fill="none" stroke="#eeedea" strokeWidth="2.5" />
        <circle
          cx="18"
          cy="18"
          r="15.9155"
          fill="none"
          stroke={BAND_STROKE[b]}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeDasharray={`${pct} 100`}
          className="transition-[stroke-dasharray] duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-semibold tracking-tight text-ink">
          {formatScore(score)}
        </span>
        <span className="text-xs text-ink-muted">{label ?? "out of 10"}</span>
      </div>
    </div>
  );
}
