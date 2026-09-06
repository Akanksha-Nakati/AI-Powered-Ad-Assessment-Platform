import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { EmptyState, ErrorMessage, Spinner } from "../../components/ui/Feedback";
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
    onSuccess: () => {
      setName("");
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

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <section className="lg:col-span-1 space-y-4">
        <div className="card glass p-5 space-y-3">
          <h2 className="text-lg font-semibold text-white">Add a brand</h2>
          <p className="text-sm text-slate-400">
            Upload your own guidelines so assessments cite them alongside general
            best practice.
          </p>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (name.trim()) create.mutate();
            }}
          >
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Brand name"
              className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 focus:border-cyan-400 focus:outline-none"
            />
            <button
              type="submit"
              disabled={!name.trim() || create.isPending}
              className="rounded-xl bg-cyan-500/20 px-4 py-2 font-medium text-cyan-100 hover:bg-cyan-500/30 disabled:opacity-50"
            >
              Add
            </button>
          </form>
          {create.isError && (
            <ErrorMessage title="Could not add brand">
              {create.error instanceof ApiError
                ? create.error.message
                : String(create.error)}
            </ErrorMessage>
          )}
        </div>

        <div className="card glass p-5 space-y-3">
          <h2 className="text-lg font-semibold text-white">Brands</h2>
          {brands.isPending && <Spinner label="Loading brands..." />}
          {brands.data?.length === 0 && (
            <p className="text-sm text-slate-400">No brands yet.</p>
          )}
          <ul className="space-y-2">
            {brands.data?.map((b) => (
              <li key={b.id}>
                <div
                  className={
                    "flex items-center justify-between rounded-xl px-3 py-2 " +
                    (selected === b.id ? "bg-cyan-500/15" : "hover:bg-white/5")
                  }
                >
                  <button
                    type="button"
                    onClick={() => setSelected(b.id)}
                    className="flex-1 text-left"
                  >
                    <span className="text-slate-100">{b.name}</span>
                    <span className="ml-2 text-xs text-slate-400">
                      {b.document_count} doc{b.document_count === 1 ? "" : "s"}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => remove.mutate(b.id)}
                    className="text-xs text-slate-500 hover:text-red-300"
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="lg:col-span-2">
        {selected ? (
          <BrandDocuments brandId={selected} />
        ) : (
          <EmptyState title="Select a brand">
            Choose a brand to upload its guidelines.
          </EmptyState>
        )}
      </section>
    </div>
  );
}
