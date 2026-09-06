import type { RetrievedChunk } from "../../lib/api/types";

type Props = {
  citations: string[];
  context: RetrievedChunk[];
};

export function CitationList({ citations, context }: Props) {
  const shown =
    citations.length > 0
      ? context.filter((c) => citations.includes(c.source))
      : context;

  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Citations</h3>
        <span className="text-xs text-slate-400">Retrieved guidance</span>
      </div>
      <div className="space-y-3">
        {shown.map((c, idx) => (
          <div key={`${c.source}-${c.chunk ?? idx}`} className="glass rounded-xl p-3">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-cyan-300">{c.source}</span>
              {c.brand_id && (
                <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-violet-200">
                  brand
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-slate-200 whitespace-pre-wrap">{c.text}</p>
          </div>
        ))}
        {shown.length === 0 && (
          <p className="text-sm text-slate-400">No citations available.</p>
        )}
      </div>
    </div>
  );
}
