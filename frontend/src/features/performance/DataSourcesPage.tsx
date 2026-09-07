import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { EmptyState, ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { Icon, icons } from "../../components/ui/Icon";
import { ApiError, api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";
import { ConnectionDetail } from "./ConnectionDetail";

const DIALECTS = ["Snowflake", "BigQuery", "Redshift", "Postgres", "Other"];

const QUERY_PLACEHOLDER =
  "SELECT ad_id AS external_ad_id, ctr, spend, conversions, impressions, " +
  "date AS metric_date\nFROM your_ad_performance_table";

export function DataSourcesPage() {
  const [name, setName] = useState("");
  const [dialect, setDialect] = useState(DIALECTS[0]);
  const [connectionUri, setConnectionUri] = useState("");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const connections = useQuery({
    queryKey: queryKeys.dataSources,
    queryFn: api.listDataSources,
  });

  const canCreate = name.trim() && connectionUri.trim() && query.trim();

  const create = useMutation({
    mutationFn: () =>
      api.createDataSource({
        name: name.trim(),
        dialect,
        connectionUri: connectionUri.trim(),
        query: query.trim(),
      }),
    onSuccess: (connection) => {
      setName("");
      setConnectionUri("");
      setQuery("");
      setSelected(connection.id);
      queryClient.invalidateQueries({ queryKey: queryKeys.dataSources });
    },
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteDataSource(id),
    onSuccess: (_, id) => {
      if (selected === id) setSelected(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.dataSources });
    },
  });

  const list = connections.data ?? [];

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-lg font-semibold text-ink">Performance</h1>
        <p className="mt-1 max-w-2xl text-sm text-ink-soft">
          Connect your own data warehouse and see whether the scores here actually
          line up with how your ads perform in the real world.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
        <section className="space-y-4">
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-ink">Connect a data source</h2>
            <p className="mt-1 text-xs text-ink-soft">
              Any query that returns external_ad_id, ctr, spend, conversions,
              impressions and metric_date.
            </p>
            <form
              className="mt-4 space-y-3"
              onSubmit={(e) => {
                e.preventDefault();
                if (canCreate) create.mutate();
              }}
            >
              <div>
                <label className="label" htmlFor="ds-name">
                  Name
                </label>
                <input
                  id="ds-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Snowflake prod"
                  className="field"
                />
              </div>
              <div>
                <label className="label" htmlFor="ds-dialect">
                  Warehouse
                </label>
                <select
                  id="ds-dialect"
                  value={dialect}
                  onChange={(e) => setDialect(e.target.value)}
                  className="field"
                >
                  {DIALECTS.map((d) => (
                    <option key={d}>{d}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label" htmlFor="ds-uri">
                  Connection string
                </label>
                <input
                  id="ds-uri"
                  type="password"
                  value={connectionUri}
                  onChange={(e) => setConnectionUri(e.target.value)}
                  placeholder="postgresql://user:password@host/database"
                  className="field font-mono text-xs"
                  autoComplete="off"
                />
                <p className="mt-1 text-xs text-ink-muted">
                  Encrypted at rest. Never shown again after saving.
                </p>
              </div>
              <div>
                <label className="label" htmlFor="ds-query">
                  Query
                </label>
                <textarea
                  id="ds-query"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={QUERY_PLACEHOLDER}
                  rows={4}
                  className="field resize-y font-mono text-xs"
                />
              </div>
              <button
                type="submit"
                disabled={!canCreate || create.isPending}
                className="btn-primary w-full"
              >
                {create.isPending ? "Connecting…" : "Connect"}
              </button>
            </form>
            {create.isError && (
              <div className="mt-3">
                <ErrorMessage title="Couldn't add that connection">
                  {create.error instanceof ApiError
                    ? create.error.message
                    : "Please try again."}
                </ErrorMessage>
              </div>
            )}
          </div>

          {connections.isPending ? (
            <div className="card p-5">
              <Spinner label="Loading connections…" />
            </div>
          ) : list.length > 0 ? (
            <ul className="card divide-y divide-line overflow-hidden">
              {list.map((c) => (
                <li key={c.id}>
                  <div
                    className={
                      "flex items-center gap-2 px-4 py-3 transition " +
                      (selected === c.id ? "bg-brand-50" : "hover:bg-canvas")
                    }
                  >
                    <button
                      type="button"
                      onClick={() => setSelected(c.id)}
                      className="min-w-0 flex-1 text-left"
                    >
                      <span className="block truncate text-sm font-medium text-ink">
                        {c.name}
                      </span>
                      <span className="text-xs text-ink-muted">
                        {c.dialect}
                        {c.last_test_ok === true && " · Connected"}
                        {c.last_test_ok === false && " · Connection failed"}
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => remove.mutate(c.id)}
                      aria-label={`Remove ${c.name}`}
                      className="rounded-lg p-1.5 text-ink-muted transition hover:bg-score-weak/10 hover:text-score-weak-ink"
                    >
                      <Icon path={icons.trash} className="h-4 w-4" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </section>

        <section>
          {selected ? (
            <ConnectionDetail
              connectionId={selected}
              connectionName={list.find((c) => c.id === selected)?.name ?? "this source"}
            />
          ) : list.length === 0 ? (
            <EmptyState title="Connect your first data source" icon={icons.target}>
              Point this at wherever your ad performance already lives, and every
              tagged check will show up here alongside how it actually did.
            </EmptyState>
          ) : (
            <EmptyState title="Select a connection" icon={icons.target}>
              Choose a data source on the left to test it, refresh its data, or see
              the correlation.
            </EmptyState>
          )}
        </section>
      </div>
    </div>
  );
}
