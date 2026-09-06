import { useCallback, useEffect, useId, useRef, useState } from "react";
import { Icon, icons } from "./Icon";

type Props = {
  files: File[];
  onChange: (files: File[]) => void;
  multiple?: boolean;
  maxFiles?: number;
  hint?: string;
};

const ACCEPT = "image/png,image/jpeg,image/webp,image/gif";

/**
 * Drag-and-drop upload with thumbnails.
 *
 * Replaces the browser's default file input, which is the single clearest
 * "this is somebody's side project" signal a web app can have.
 */
export function UploadZone({
  files,
  onChange,
  multiple = false,
  maxFiles = 5,
  hint,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const inputId = useId();

  const accept = useCallback(
    (incoming: FileList | null) => {
      if (!incoming) return;
      const images = Array.from(incoming).filter((f) => f.type.startsWith("image/"));
      onChange(multiple ? [...files, ...images].slice(0, maxFiles) : images.slice(0, 1));
    },
    [files, multiple, maxFiles, onChange],
  );

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          accept(e.dataTransfer.files);
        }}
        className={
          "relative rounded-xl2 border-2 border-dashed p-6 text-center transition " +
          (dragging
            ? "border-brand-600 bg-brand-50"
            : "border-line bg-canvas hover:border-brand-300 hover:bg-brand-50/40")
        }
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept={ACCEPT}
          multiple={multiple}
          onChange={(e) => {
            accept(e.target.files);
            // Allow re-selecting the same file after a reset.
            e.target.value = "";
          }}
          className="sr-only"
        />
        <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-brand-100 text-brand-700">
          <Icon path={icons.upload} className="h-5 w-5" />
        </div>
        <label
          htmlFor={inputId}
          className="cursor-pointer text-sm font-semibold text-brand-700 hover:text-brand-800"
        >
          Choose {multiple ? "images" : "an image"}
        </label>
        <p className="mt-1 text-sm text-ink-muted">
          or drag and drop &middot; PNG, JPG, WebP
        </p>
        {hint && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
      </div>

      {files.length > 0 && (
        <ul className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {files.map((file, index) => (
            <Thumb
              key={`${file.name}-${index}`}
              file={file}
              onRemove={() => onChange(files.filter((_, i) => i !== index))}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function Thumb({ file, onRemove }: { file: File; onRemove: () => void }) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  return (
    <li className="group relative overflow-hidden rounded-xl border border-line bg-white">
      {url && (
        <img src={url} alt={file.name} className="h-24 w-full object-cover" />
      )}
      <p className="truncate px-2 py-1.5 text-xs text-ink-soft" title={file.name}>
        {file.name}
      </p>
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${file.name}`}
        className="absolute right-1.5 top-1.5 rounded-full bg-white/90 p-1 text-ink-soft shadow-card transition hover:text-score-weak-ink"
      >
        <Icon path="M18 6 6 18M6 6l12 12" className="h-3.5 w-3.5" />
      </button>
    </li>
  );
}
