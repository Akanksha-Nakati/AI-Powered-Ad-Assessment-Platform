import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { ErrorMessage, Spinner } from "../../components/ui/Feedback";
import { ApiError, api } from "../../lib/api/client";
import { queryKeys } from "../../lib/query";

export function BrandDocuments({ brandId }: { brandId: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
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
      // The brand's document count changed.
      queryClient.invalidateQueries({ queryKey: queryKeys.brands });
    },
  });

  return (
    <div className="card glass p-5 space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-white">Brand documents</h2>
        <p className="text-sm text-slate-400">
          Markdown or plain text. Chunks are embedded and retrieved alongside the
          general marketing corpus.
        </p>
      </div>

      <div className="rounded-2xl border border-dashed border-cyan-500/50 bg-cyan-500/5 p-4">
        <input
          ref={inputRef}
          type="file"
          accept=".md,.markdown,.txt"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload.mutate(file);
          }}
          className="text-sm text-slate-200"
        />
      </div>

      {upload.isPending && <Spinner label="Embedding document..." />}
      {upload.isError && (
        <ErrorMessage title="Upload failed">
          {upload.error instanceof ApiError
            ? upload.error.message
            : String(upload.error)}
        </ErrorMessage>
      )}

      {documents.isPending ? (
        <Spinner label="Loading documents..." />
      ) : documents.data?.length ? (
        <ul className="divide-y divide-white/5">
          {documents.data.map((d) => (
            <li key={d.id} className="flex items-center justify-between py-2 text-sm">
              <span className="text-slate-100">{d.filename}</span>
              <span className="text-xs text-slate-400">{d.chunk_count} chunks</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-400">No documents uploaded yet.</p>
      )}
    </div>
  );
}
