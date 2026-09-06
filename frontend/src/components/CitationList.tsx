type Props = {
  citations: string[];
  context: { text: string; source: string; chunk?: number }[];
};

export function CitationList({ citations, context }: Props) {
  const filtered =
    citations.length > 0
      ? context.filter((c) => citations.includes(c.source))
      : context;

  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Citations</h3>
        <span className="text-xs text-slate-400">RAG snippets</span>
      </div>
      <div className="space-y-3">
        {filtered.map((c, idx) => (
          <div key={`${c.source}-${c.chunk ?? idx}`} className="glass rounded-xl p-3">
            <div className="text-xs text-cyan-300">{c.source}</div>
            <p className="text-sm text-slate-200 whitespace-pre-wrap">{c.text}</p>
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="text-sm text-slate-400">No citations available.</p>
        )}
      </div>
    </div>
  );
}

