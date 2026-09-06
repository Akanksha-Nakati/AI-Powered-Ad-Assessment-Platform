import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { EmptyState, ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { Icon, icons } from "../../components/ui/Icon";
import { ApiError, api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";
import { BrandDocuments } from "./BrandDocuments";

export function BrandsPage() {
  const [name, setName] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const brands = useQuery({ queryKey: queryKeys.brands, queryFn: api.listBrands });

  const create = useMutation({
    mutationFn: () => api.createBrand(name.trim()),
    onSuccess: (brand) => {
      setName("");
      setSelected(brand.id);
      queryClient.invalidateQueries({ queryKey: queryKeys.brands });
    },
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteBrand(id),
    onSuccess: (_, id) => {
      if (selected === id) setSelected(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.brands });
    },
  });

  const list = brands.data ?? [];

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-lg font-semibold text-ink">Brand rules</h1>
        <p className="mt-1 max-w-2xl text-sm text-ink-soft">
          Add your brand guidelines once and every ad you check will also be checked
          against them — tone of voice, colours, logo placement, claims you can't make.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,340px)_minmax(0,1fr)]">
        <section className="space-y-4">
          <div className="card p-5">
            <label className="label" htmlFor="brand-name">
              Add a brand
            </label>
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                if (name.trim()) create.mutate();
              }}
            >
              <input
                id="brand-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Nimbus Bedding"
                className="field flex-1"
              />
              <button
                type="submit"
                disabled={!name.trim() || create.isPending}
                className="btn-primary shrink-0 px-3"
                aria-label="Add brand"
              >
                <Icon path={icons.plus} className="h-4 w-4" />
              </button>
            </form>
            {create.isError && (
              <div className="mt-3">
                <ErrorMessage title="Couldn't add that brand">
                  {create.error instanceof ApiError
                    ? create.error.message
                    : "Please try again."}
                </ErrorMessage>
              </div>
            )}
          </div>

          {brands.isPending ? (
            <div className="card p-5">
              <Spinner label="Loading brands…" />
            </div>
          ) : list.length > 0 ? (
            <ul className="card divide-y divide-line overflow-hidden">
              {list.map((b) => (
                <li key={b.id}>
                  <div
                    className={
                      "flex items-center gap-2 px-4 py-3 transition " +
                      (selected === b.id ? "bg-brand-50" : "hover:bg-canvas")
                    }
                  >
                    <button
                      type="button"
                      onClick={() => setSelected(b.id)}
                      className="min-w-0 flex-1 text-left"
                    >
                      <span className="block truncate text-sm font-medium text-ink">
                        {b.name}
                      </span>
                      <span className="text-xs text-ink-muted">
                        {b.document_count === 0
                          ? "No guidelines yet"
                          : `${b.document_count} document${b.document_count === 1 ? "" : "s"}`}
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => remove.mutate(b.id)}
                      aria-label={`Remove ${b.name}`}
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
            <BrandDocuments
              brandId={selected}
              brandName={list.find((b) => b.id === selected)?.name ?? "this brand"}
            />
          ) : list.length === 0 ? (
            <EmptyState title="Add your first brand" icon={icons.book}>
              Give it a name, then upload your guidelines. Anything you'd tell a new
              designer on their first day works well.
            </EmptyState>
          ) : (
            <EmptyState title="Select a brand" icon={icons.book}>
              Choose a brand on the left to upload or review its guidelines.
            </EmptyState>
          )}
        </section>
      </div>
    </div>
  );
}
