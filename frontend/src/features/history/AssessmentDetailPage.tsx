import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { ScorecardPanel } from "../assess/ScorecardPanel";
import { api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";

export function AssessmentDetailPage() {
  const { id = "" } = useParams();
  const assessment = useQuery({
    queryKey: queryKeys.assessment(id),
    queryFn: () => api.getAssessment(id),
    enabled: Boolean(id),
  });

  if (assessment.isPending) return <Spinner label="Loading assessment..." />;
  if (assessment.isError)
    return (
      <ErrorMessage title="Could not load that assessment">
        {String(assessment.error)}
      </ErrorMessage>
    );

  return (
    <div className="space-y-4">
      <Link to="/history" className="text-sm text-cyan-300 hover:text-cyan-200">
        &larr; Back to history
      </Link>
      <ScorecardPanel assessment={assessment.data} />
    </div>
  );
}
