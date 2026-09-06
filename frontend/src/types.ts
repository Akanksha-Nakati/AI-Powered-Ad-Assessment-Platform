export type ScoreKeys =
  | "attention"
  | "clarity"
  | "targeting"
  | "cta"
  | "branding"
  | "value";

export type AssessmentResponse = {
  scores: Partial<Record<ScoreKeys, number>>;
  overall_score: number;
  feedback: string;
  recommendations: string[];
  citations: string[];
  context: { text: string; source: string; chunk?: number }[];
  gemini: Record<string, unknown>;
};

