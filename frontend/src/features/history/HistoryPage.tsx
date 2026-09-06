import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { EmptyState, ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";

export function HistoryPage() {
  const history = useQuery({
    queryKey: queryKeys.assessments,
    queryFn: () => api.listAssessments(50),
  });

  if (history.isPending) return <Spinner label="Loading history..." />;
  if (history.isError)
    return <ErrorMessage title="Could not load history">{String(history.error)}</ErrorMessage>;
  if (!history.data.length)
    return (
      <EmptyState title="No assessments yet">
        Assessments you run will be listed here.
      </EmptyState>
    );

  return (
    <div className="card glass overflow-hidden">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-400">
          <tr>
            <th className="px-5 py-3">When</th>
            <th className="px-5 py-3">Placement</th>
            <th className="px-5 py-3">Score</th>
            <th className="px-5 py-3" />
          </tr>
        </thead>
        <tbody>
          {history.data.map((a) => (
            <tr key={a.id} className="border-b border-white/5 last:border-0">
              <td className="px-5 py-3 text-slate-300">
                {new Date(a.created_at).toLocaleString()}
              </td>
              <td className="px-5 py-3 text-slate-200">
                {a.metadata.platform} &middot; {a.metadata.industry} &middot;{" "}
                {a.metadata.ad_type}
              </td>
              <td className="px-5 py-3 font-semibold text-white">
                {a.scorecard.overall_score.toFixed(1)}
              </td>
              <td className="px-5 py-3 text-right">
                <Link
                  to={`/history/${a.id}`}
                  className="text-cyan-300 hover:text-cyan-200"
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
