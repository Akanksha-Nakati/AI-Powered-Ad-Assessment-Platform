/**
 * Domain types, re-exported from the generated OpenAPI schema.
 *
 * These used to be hand-written in src/types.ts and drifted from the backend
 * silently -- a renamed field showed up as a blank panel at runtime rather than
 * a build error. Regenerate with `npm run gen:api` after changing the API.
 */
import type { components } from "./schema";

export type Assessment = components["schemas"]["Assessment"];
export type AdScorecard = components["schemas"]["AdScorecard"];
export type AdMetadata = components["schemas"]["AdMetadata"];
export type VisualAnalysis = components["schemas"]["VisualAnalysis"];
export type RetrievedChunk = components["schemas"]["RetrievedChunk"];
export type Brand = components["schemas"]["Brand"];
export type KnowledgeDocument = components["schemas"]["KnowledgeDocument"];
export type Comparison = components["schemas"]["Comparison"];
export type ComparisonEntry = components["schemas"]["ComparisonEntry"];
export type Criterion = components["schemas"]["Criterion"];

/** Display order for the six criteria. */
export const CRITERIA: Criterion[] = [
  "attention",
  "clarity",
  "targeting",
  "cta",
  "branding",
  "value",
];

export const CRITERION_LABELS: Record<Criterion, string> = {
  attention: "Attention",
  clarity: "Clarity",
  targeting: "Targeting",
  cta: "CTA",
  branding: "Branding",
  value: "Value",
};
