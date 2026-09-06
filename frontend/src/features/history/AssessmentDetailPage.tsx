import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";
import { ScorecardPanel } from "../assess/ScorecardPanel";

export function AssessmentDetailPage() {
  const { id = "" } = useParams();
  const assessment = useQuery({
    queryKey: queryKeys.assessment(id),
    queryFn: () => api.getAssessment(id),
    enabled: Boolean(id),
  });

  return (
    <div className="space-y-5">
      <Link
        to="/app/history"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-soft hover:text-ink"
      >
        <Icon path="M19 12H5m6 6-6-6 6-6" className="h-4 w-4" />
        Back to your checks
      </Link>

      {assessment.isPending && (
        <div className="card p-6">
          <Spinner label="Loading…" />
        </div>
      )}
      {assessment.isError && (
        <ErrorMessage title="We couldn't find that check">
          It may have been removed.
        </ErrorMessage>
      )}
      {assessment.data && <ScorecardPanel assessment={assessment.data} />}
    </div>
  );
}
