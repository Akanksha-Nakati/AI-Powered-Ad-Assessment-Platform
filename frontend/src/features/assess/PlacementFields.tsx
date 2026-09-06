import type { Brand } from "../../lib/api/types";

export const PLATFORMS = ["Facebook/IG", "TikTok", "YouTube", "LinkedIn", "Display"];
export const INDUSTRIES = ["Ecommerce", "SaaS", "Finance", "Health/Wellness", "Education"];
export const AD_TYPES = ["Static Image", "Carousel", "Story/Reel", "Banner"];

export type Placement = {
  platform: string;
  industry: string;
  adType: string;
  brandId: string;
};

export const DEFAULT_PLACEMENT: Placement = {
  platform: PLATFORMS[0],
  industry: INDUSTRIES[0],
  adType: AD_TYPES[0],
  brandId: "",
};

const selectClass =
  "w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 focus:border-cyan-400 focus:outline-none";

type Props = {
  value: Placement;
  onChange: (next: Placement) => void;
  brands: Brand[];
};

export function PlacementFields({ value, onChange, brands }: Props) {
  const field = (key: keyof Placement) => (
    e: React.ChangeEvent<HTMLSelectElement>,
  ) => onChange({ ...value, [key]: e.target.value });

  return (
    <div className="grid grid-cols-1 gap-3">
      <label className="space-y-1 block">
        <span className="text-sm text-slate-200">Platform</span>
        <select className={selectClass} value={value.platform} onChange={field("platform")}>
          {PLATFORMS.map((p) => (
            <option key={p}>{p}</option>
          ))}
        </select>
      </label>

      <label className="space-y-1 block">
        <span className="text-sm text-slate-200">Industry</span>
        <select className={selectClass} value={value.industry} onChange={field("industry")}>
          {INDUSTRIES.map((p) => (
            <option key={p}>{p}</option>
          ))}
        </select>
      </label>

      <label className="space-y-1 block">
        <span className="text-sm text-slate-200">Ad Type</span>
        <select className={selectClass} value={value.adType} onChange={field("adType")}>
          {AD_TYPES.map((p) => (
            <option key={p}>{p}</option>
          ))}
        </select>
      </label>

      <label className="space-y-1 block">
        <span className="text-sm text-slate-200">
          Brand <span className="text-slate-500">(optional)</span>
        </span>
        <select className={selectClass} value={value.brandId} onChange={field("brandId")}>
          <option value="">General best practices only</option>
          {brands.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
