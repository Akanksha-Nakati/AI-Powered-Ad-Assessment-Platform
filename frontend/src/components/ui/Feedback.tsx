import type { ReactNode } from "react";
import { Icon, icons } from "./Icon";

export function ErrorMessage({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-xl border border-score-weak/30 bg-score-weak/5 p-4" role="alert">
      <p className="flex items-center gap-2 text-sm font-semibold text-score-weak-ink">
        <Icon path="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
        {title}
      </p>
      {children && <p className="mt-1 text-sm text-score-weak-ink/80">{children}</p>}
    </div>
  );
}

export function EmptyState({
  title,
  children,
  icon = icons.image,
  action,
}: {
  title: string;
  children?: ReactNode;
  icon?: string;
  action?: ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center px-6 py-14 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
        <Icon path={icon} className="h-5 w-5" />
      </div>
      <p className="text-base font-semibold text-ink">{title}</p>
      {children && <p className="mt-1.5 max-w-sm text-sm text-ink-soft">{children}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Spinner({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
      <span className="text-sm text-ink-soft">{label}</span>
    </div>
  );
}

/** Shown while an assessment runs — a real wait of several seconds. */
export function AnalysingCard({ note }: { note: string }) {
  return (
    <div className="card overflow-hidden p-6">
      <Spinner label={note} />
      <div className="mt-5 space-y-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="relative overflow-hidden rounded-full bg-black/[0.05]">
            <div className="h-2.5" />
            <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-black/[0.06] to-transparent" />
          </div>
        ))}
      </div>
    </div>
  );
}
