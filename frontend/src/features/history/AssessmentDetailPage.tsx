import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { ApiError, api } from "../../lib/api/client";
import type { Assessment } from "../../lib/api/types";
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
      {assessment.data && (
        <>
          <TagForPerformance assessment={assessment.data} />
          <ScorecardPanel assessment={assessment.data} />
        </>
      )}
    </div>
  );
}

function TagForPerformance({ assessment }: { assessment: Assessment }) {
  const [value, setValue] = useState(assessment.external_ad_id ?? "");
  const queryClient = useQueryClient();

  const save = useMutation({
    mutationFn: () => api.tagAssessment(assessment.id, value.trim() || null),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.assessment(assessment.id), updated);
    },
  });

  const dirty = value.trim() !== (assessment.external_ad_id ?? "");

  return (
    <div className="card p-5">
      <label className="label" htmlFor="external-ad-id">
        Tag for performance tracking
      </label>
      <p className="mt-1 text-sm text-ink-soft">
        Give this ad the same identifier it has in your own data warehouse, and
        it'll show up in the Performance tab once you connect one.
      </p>
      <form
        className="mt-3 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (dirty) save.mutate();
        }}
      >
        <input
          id="external-ad-id"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="e.g. campaign-42"
          className="field flex-1"
        />
        <button
          type="submit"
          disabled={!dirty || save.isPending}
          className="btn-primary shrink-0 px-4"
        >
          {save.isPending ? "Saving…" : "Save"}
        </button>
      </form>
      {save.isError && (
        <div className="mt-3">
          <ErrorMessage title="Couldn't save that tag">
            {save.error instanceof ApiError
              ? save.error.message
              : "Please try again."}
          </ErrorMessage>
        </div>
      )}
    </div>
  );
}
