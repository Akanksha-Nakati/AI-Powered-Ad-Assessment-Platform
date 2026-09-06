import type { Brand } from "../../lib/api/types";

export const PLATFORMS = ["Facebook/IG", "TikTok", "YouTube", "LinkedIn", "Display"];
export const INDUSTRIES = [
  "Ecommerce",
  "SaaS",
  "Finance",
  "Health/Wellness",
  "Education",
];
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

type Props = {
  value: Placement;
  onChange: (next: Placement) => void;
  brands: Brand[];
};

export function PlacementFields({ value, onChange, brands }: Props) {
  const set = (key: keyof Placement) => (e: React.ChangeEvent<HTMLSelectElement>) =>
    onChange({ ...value, [key]: e.target.value });

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="label" htmlFor="platform">Where will it run?</label>
          <select id="platform" className="field" value={value.platform} onChange={set("platform")}>
            {PLATFORMS.map((p) => <option key={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="adType">Format</label>
          <select id="adType" className="field" value={value.adType} onChange={set("adType")}>
            {AD_TYPES.map((p) => <option key={p}>{p}</option>)}
          </select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="label" htmlFor="industry">Industry</label>
          <select id="industry" className="field" value={value.industry} onChange={set("industry")}>
            {INDUSTRIES.map((p) => <option key={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="brand">
            Brand rules <span className="font-normal text-ink-muted">(optional)</span>
          </label>
          <select id="brand" className="field" value={value.brandId} onChange={set("brandId")}>
            <option value="">Don't check brand rules</option>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
