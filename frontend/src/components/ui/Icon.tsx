type Props = { path: string; className?: string; filled?: boolean };

/** Minimal stroke icon. Paths live at the call site so there is no icon table. */
export function Icon({ path, className = "h-4 w-4", filled = false }: Props) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke={filled ? "none" : "currentColor"}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  );
}

export const icons = {
  check: "M20 6 9 17l-5-5",
  upload: "M12 16V4m0 0L8 8m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2",
  image: "M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zm2 12 4-4 3 3 4-5 4 6",
  spark: "m12 3 2.1 5.7L20 10.8l-5.9 2.1L12 19l-2.1-6.1L4 10.8l5.9-2.1z",
  layers: "m12 2 9 5-9 5-9-5zM3 12l9 5 9-5M3 17l9 5 9-5",
  clock: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 6v6l4 2",
  book: "M4 4a2 2 0 0 1 2-2h12v18H6a2 2 0 0 0-2 2zM6 16h12",
  arrowRight: "M5 12h14m-6-6 6 6-6 6",
  trash: "M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6",
  plus: "M12 5v14M5 12h14",
  chevronDown: "m6 9 6 6 6-6",
  target: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zm0-4a6 6 0 1 0 0-12 6 6 0 0 0 0 12zm0-4a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
};
