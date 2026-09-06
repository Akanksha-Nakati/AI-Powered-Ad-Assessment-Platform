import { useEffect, useState } from "react";

type Props = {
  file: File | null;
  onChange: (file: File | null) => void;
  label?: string;
};

export function ImagePicker({ file, onChange, label = "Ad Image" }: Props) {
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    // Object URLs leak until revoked; the original code created one per
    // selection and never released any of them.
    return () => URL.revokeObjectURL(url);
  }, [file]);

  return (
    <div>
      <span className="text-sm text-slate-200">{label}</span>
      <div className="mt-2 flex flex-col gap-3 rounded-2xl border border-dashed border-cyan-500/50 bg-cyan-500/5 p-4">
        <input
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          onChange={(e) => onChange(e.target.files?.[0] ?? null)}
          className="text-sm text-slate-200"
        />
        {preview && (
          <img
            src={preview}
            alt="Selected ad preview"
            className="h-48 w-full rounded-xl border border-cyan-500/40 object-cover"
          />
        )}
      </div>
    </div>
  );
}
