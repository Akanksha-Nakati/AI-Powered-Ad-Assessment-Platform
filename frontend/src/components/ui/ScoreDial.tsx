type Props = { score: number | null | undefined; size?: number };

export function ScoreDial({ score, size = 112 }: Props) {
  const pct = score ? Math.round((score / 10) * 100) : 0;
  return (
    <div className="relative" style={{ height: size, width: size }}>
      <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
        <path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke="#1e293b"
          strokeWidth="3"
        />
        <path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831"
          fill="none"
          stroke="url(#scoreDialGradient)"
          strokeWidth="3"
          strokeDasharray={`${pct}, 100`}
        />
        <defs>
          <linearGradient id="scoreDialGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="50%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex items-center justify-center text-lg font-semibold">
        {pct}%
      </div>
    </div>
  );
}
