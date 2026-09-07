import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { Icon, icons } from "../../components/ui/Icon";
import { ApiError, api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";
import { CorrelationChart } from "./CorrelationChart";

type Props = { connectionId: string; connectionName: string };

export function ConnectionDetail({ connectionId, connectionName }: Props) {
  const queryClient = useQueryClient();

  const correlation = useQuery({
    queryKey: queryKeys.correlation(connectionId),
    queryFn: () => api.getCorrelation(connectionId),
  });

  const test = useMutation({
    mutationFn: () => api.testDataSource(connectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.dataSources });
    },
  });

  const refresh = useMutation({
    mutationFn: () => api.refreshDataSource(connectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.correlation(connectionId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.dataSources });
    },
  });

  return (
    <div className="space-y-5">
      <div className="card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-ink">{connectionName}</h2>
            <p className="mt-1 text-sm text-ink-soft">
              Test the connection, then pull the latest performance numbers.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => test.mutate()}
              disabled={test.isPending}
              className="btn-secondary"
            >
              {test.isPending ? "Testing…" : "Test connection"}
            </button>
            <button
              type="button"
              onClick={() => refresh.mutate()}
              disabled={refresh.isPending}
              className="btn-primary"
            >
              {refresh.isPending ? "Refreshing…" : "Refresh data"}
            </button>
          </div>
        </div>

        {test.isSuccess && (
          <p className="mt-4 flex items-center gap-1.5 text-sm text-score-strong-ink">
            <Icon path={icons.check} className="h-4 w-4" />
            Connected successfully.
          </p>
        )}
        {test.isError && (
          <div className="mt-4">
            <ErrorMessage title="Couldn't connect">
              {test.error instanceof ApiError ? test.error.message : "Please try again."}
            </ErrorMessage>
          </div>
        )}

        {refresh.isSuccess && (
          <p className="mt-4 text-sm text-ink-soft">
            Pulled {refresh.data.rows_fetched} row
            {refresh.data.rows_fetched === 1 ? "" : "s"}.
          </p>
        )}
        {refresh.isError && (
          <div className="mt-4">
            <ErrorMessage title="Couldn't refresh">
              {refresh.error instanceof ApiError
                ? refresh.error.message
                : "Please try again."}
            </ErrorMessage>
          </div>
        )}
      </div>

      {correlation.isPending ? (
        <div className="card p-6">
          <Spinner label="Loading correlation…" />
        </div>
      ) : correlation.isError ? (
        <ErrorMessage title="Couldn't load the correlation">
          {correlation.error instanceof ApiError
            ? correlation.error.message
            : "Please try again."}
        </ErrorMessage>
      ) : correlation.data ? (
        <CorrelationChart result={correlation.data} />
      ) : null}
    </div>
  );
}
