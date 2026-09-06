/**
 * Presentation rules for scores and sources.
 *
 * This module is where the system's internal vocabulary is translated into
 * something a marketer would say. Nothing user-facing should mention retrieval,
 * embeddings, chunks or model names.
 */
import type { Criterion, RetrievedChunk } from "./api/types";

/** What each criterion is called, and what it actually means, in plain terms. */
export const CRITERION_COPY: Record<Criterion, { label: string; blurb: string }> = {
  attention: {
    label: "Stops the scroll",
    blurb: "Whether the creative earns a second of attention in a busy feed.",
  },
  clarity: {
    label: "Clear message",
    blurb: "Whether the offer is understandable at a glance.",
  },
  targeting: {
    label: "Right audience",
    blurb: "How well the creative fits the channel and the people on it.",
  },
  cta: {
    label: "Call to action",
    blurb: "Whether there is one obvious next step.",
  },
  branding: {
    label: "Brand presence",
    blurb: "Whether viewers will remember who the ad was for.",
  },
  value: {
    label: "Value proposition",
    blurb: "Whether a concrete benefit or proof point comes across.",
  },
};

export type Band = "strong" | "mid" | "weak";

/**
 * Three bands rather than a continuous colour ramp: a reader needs to know
 * "is this fine or not", and three states is the most a glance can carry.
 */
export function band(score: number): Band {
  if (score >= 7) return "strong";
  if (score >= 4) return "mid";
  return "weak";
}

/**
 * Status colour never carries meaning alone -- every band ships with a label
 * and an icon. The mid band's amber is deliberately sub-3:1 on white, so the
 * text token differs from the mark token.
 */
export const BAND_STYLE: Record<
  Band,
  { label: string; mark: string; text: string; chip: string; icon: string }
> = {
  strong: {
    label: "Strong",
    mark: "bg-score-strong",
    text: "text-score-strong-ink",
    chip: "bg-score-strong/10 text-score-strong-ink",
    icon: "M20 6 9 17l-5-5",
  },
  mid: {
    label: "Needs work",
    mark: "bg-score-mid",
    text: "text-score-mid-ink",
    chip: "bg-score-mid/15 text-score-mid-ink",
    icon: "M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z",
  },
  weak: {
    label: "Weak",
    mark: "bg-score-weak",
    text: "text-score-weak-ink",
    chip: "bg-score-weak/10 text-score-weak-ink",
    icon: "M18 6 6 18M6 6l12 12",
  },
};

/** A one-line verdict for the headline number. */
export function overallVerdict(score: number): string {
  if (score >= 8) return "Ready to run";
  if (score >= 7) return "Strong, with room to sharpen";
  if (score >= 5.5) return "Promising, but needs work";
  if (score >= 4) return "Needs work before running";
  return "Not ready to run";
}

/**
 * Source files carry internal names. Show something a person would recognise,
 * and never the file extension.
 */
const SOURCE_NAMES: Record<string, string> = {
  "AIDA.md": "Attention & persuasion",
  "Color_Psychology.md": "Colour psychology",
  "CTA_Best_Practices.md": "Call-to-action best practice",
};

export function sourceLabel(chunk: Pick<RetrievedChunk, "source" | "brand_id">): string {
  if (chunk.brand_id) {
    return chunk.source.replace(/\.(md|markdown|txt)$/i, "").replace(/[-_]/g, " ");
  }
  return (
    SOURCE_NAMES[chunk.source] ??
    chunk.source.replace(/\.(md|markdown|txt)$/i, "").replace(/[-_]/g, " ")
  );
}

export function formatScore(score: number): string {
  return score.toFixed(1);
}
