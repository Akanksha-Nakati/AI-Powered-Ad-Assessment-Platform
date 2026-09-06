import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { EmptyState, ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { Icon, icons } from "../../components/ui/Icon";
import { api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";
import { band, BAND_STYLE, formatScore } from "../../lib/scoring";

function relativeDate(iso: string): string {
  const then = new Date(iso);
  const mins = Math.round((Date.now() - then.getTime()) / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  if (mins < 60 * 24) return `${Math.round(mins / 60)}h ago`;
  return then.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function HistoryPage() {
  const history = useQuery({
    queryKey: queryKeys.assessments,
    queryFn: () => api.listAssessments(50),
  });

  if (history.isPending) {
    return (
      <div className="card p-6">
        <Spinner label="Loading your checks…" />
      </div>
    );
  }

  if (history.isError) {
    return (
      <ErrorMessage title="We couldn't load your history">
        Please refresh and try again.
      </ErrorMessage>
    );
  }

  if (!history.data.length) {
    return (
      <EmptyState
        title="No checks yet"
        icon={icons.clock}
        action={
          <Link to="/app" className="btn-primary">
            Check an ad
          </Link>
        }
      >
        Every ad you check is saved here, so you can look back at what you changed
        and how the scores moved.
      </EmptyState>
    );
  }

  return (
    <div>
      <h1 className="text-lg font-semibold text-ink">Your checks</h1>
      <p className="mt-1 text-sm text-ink-soft">
        {history.data.length} {history.data.length === 1 ? "ad" : "ads"} checked
      </p>

      <ul className="mt-6 space-y-3">
        {history.data.map((a) => {
          const style = BAND_STYLE[band(a.scorecard.overall_score)];
          return (
            <li key={a.id}>
              <Link
                to={`/app/history/${a.id}`}
                className="card flex items-center gap-4 p-4 transition hover:shadow-lift"
              >
                <span
                  className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-base font-semibold tabular-nums ${style.chip}`}
                >
                  {formatScore(a.scorecard.overall_score)}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-ink">
                    {a.metadata.platform} &middot; {a.metadata.ad_type}
                  </span>
                  <span className="mt-0.5 block truncate text-sm text-ink-soft">
                    {a.scorecard.feedback}
                  </span>
                </span>
                <span className="hidden shrink-0 text-xs text-ink-muted sm:block">
                  {relativeDate(a.created_at)}
                </span>
                <Icon path={icons.arrowRight} className="h-4 w-4 shrink-0 text-ink-muted" />
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
