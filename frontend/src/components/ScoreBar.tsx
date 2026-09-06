import { ScoreKeys } from "../types";

type Props = {
  label: ScoreKeys;
  value?: number;
};

const labels: Record<ScoreKeys, string> = {
  attention: "Attention",
  clarity: "Clarity",
  targeting: "Targeting",
  cta: "CTA",
  branding: "Branding",
  value: "Value",
};

export function ScoreBar({ label, value }: Props) {
  const pct = value !== undefined ? Math.round((value / 10) * 100) : 0;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm text-slate-200">
        <span>{labels[label]}</span>
        <span className="font-semibold">{value !== undefined ? value.toFixed(1) : "-"}/10</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-blue-500 to-violet-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

