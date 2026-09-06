import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useId, useRef, useState } from "react";
import { ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { Icon, icons } from "../../components/ui/Icon";
import { ApiError, api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";

type Props = { brandId: string; brandName: string };

export function BrandDocuments({ brandId, brandName }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();
  const [dragging, setDragging] = useState(false);
  const queryClient = useQueryClient();

  const documents = useQuery({
    queryKey: queryKeys.documents(brandId),
    queryFn: () => api.listDocuments(brandId),
  });

  const upload = useMutation({
    mutationFn: (file: File) => api.uploadDocument(brandId, file),
    onSuccess: () => {
      if (inputRef.current) inputRef.current.value = "";
      queryClient.invalidateQueries({ queryKey: queryKeys.documents(brandId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.brands });
    },
  });

  return (
    <div className="card p-6">
      <h2 className="text-base font-semibold text-ink">Guidelines for {brandName}</h2>
      <p className="mt-1 text-sm text-ink-soft">
        Upload a text or Markdown file. Tone of voice, colour rules, logo placement,
        claims to avoid — whatever a designer would need to get it right.
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) upload.mutate(file);
        }}
        className={
          "mt-5 rounded-xl2 border-2 border-dashed p-6 text-center transition " +
          (dragging
            ? "border-brand-600 bg-brand-50"
            : "border-line bg-canvas hover:border-brand-300")
        }
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept=".md,.markdown,.txt,text/plain,text/markdown"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload.mutate(file);
          }}
          className="sr-only"
        />
        <label
          htmlFor={inputId}
          className="cursor-pointer text-sm font-semibold text-brand-700 hover:text-brand-800"
        >
          Choose a file
        </label>
        <p className="mt-1 text-sm text-ink-muted">or drag it here &middot; TXT or MD</p>
      </div>

      {upload.isPending && (
        <div className="mt-4">
          <Spinner label="Saving your guidelines…" />
        </div>
      )}
      {upload.isError && (
        <div className="mt-4">
          <ErrorMessage title="Upload failed">
            {upload.error instanceof ApiError
              ? upload.error.message
              : "Please try again."}
          </ErrorMessage>
        </div>
      )}

      <div className="mt-6">
        {documents.isPending ? (
          <Spinner label="Loading…" />
        ) : documents.data?.length ? (
          <ul className="divide-y divide-line">
            {documents.data.map((d) => (
              <li key={d.id} className="flex items-center gap-3 py-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                  <Icon path={icons.book} className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-ink">
                    {d.filename.replace(/\.(md|markdown|txt)$/i, "")}
                  </span>
                  <span className="text-xs text-ink-muted">
                    Added {new Date(d.created_at).toLocaleDateString()}
                  </span>
                </span>
                <span className="flex items-center gap-1.5 rounded-full bg-score-strong/10 px-2.5 py-1 text-xs font-medium text-score-strong-ink">
                  <Icon path={icons.check} className="h-3 w-3" />
                  Active
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-ink-muted">
            No guidelines uploaded yet. Checks will use general best practice only.
          </p>
        )}
      </div>
    </div>
  );
}
