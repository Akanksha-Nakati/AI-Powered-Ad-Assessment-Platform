type MessageProps = { title: string; children?: React.ReactNode };

export function ErrorMessage({ title, children }: MessageProps) {
  return (
    <div className="card border-red-500/40 bg-red-500/10 p-4">
      <p className="font-semibold text-red-200">{title}</p>
      {children && <p className="mt-1 text-sm text-red-100/80">{children}</p>}
    </div>
  );
}

export function EmptyState({ title, children }: MessageProps) {
  return (
    <div className="card glass p-6 text-slate-300">
      <p className="font-medium text-slate-100">{title}</p>
      {children && <p className="mt-1 text-sm text-slate-400">{children}</p>}
    </div>
  );
}

export function Spinner({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 text-slate-300">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
