import { Link } from "react-router-dom";
import { Icon, icons } from "../../components/ui/Icon";
import { ScoreMeter } from "../../components/ui/ScoreMeter";
import { ScoreRing } from "../../components/ui/ScoreRing";
import type { Criterion } from "../../lib/api/types";
import { CRITERION_COPY } from "../../lib/scoring";

/** A representative result, so the value is visible before committing to anything. */
const SAMPLE: { criterion: Criterion; score: number }[] = [
  { criterion: "attention", score: 3.0 },
  { criterion: "clarity", score: 7.5 },
  { criterion: "cta", score: 8.5 },
  { criterion: "branding", score: 2.0 },
];

const ALL_CRITERIA: Criterion[] = [
  "attention",
  "clarity",
  "targeting",
  "cta",
  "branding",
  "value",
];

export function LandingPage() {
  return (
    <main>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 -top-40 h-[420px] bg-[radial-gradient(60%_60%_at_50%_50%,rgba(74,58,167,0.10),transparent_70%)]"
        />
        <div className="container-page relative grid items-center gap-14 py-16 lg:grid-cols-2 lg:py-24">
          <div className="animate-fade-up">
            <span className="inline-flex items-center gap-2 rounded-full border border-line bg-white px-3 py-1 text-xs font-medium text-ink-soft">
              <Icon path={icons.spark} className="h-3.5 w-3.5 text-brand-600" />
              Feedback in about ten seconds
            </span>

            <h1 className="mt-5 text-display font-semibold text-ink">
              Know if your ad works
              <span className="text-brand-600"> before you pay for it</span>
            </h1>

            <p className="mt-5 max-w-lg text-lg leading-relaxed text-ink-soft">
              Upload a creative and get an honest critique in seconds: what's working,
              what will cost you clicks, and exactly what to change. Add your brand
              rules and every review checks against those too.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link to="/app" className="btn-primary px-5 py-3 text-base">
                Check an ad
                <Icon path={icons.arrowRight} className="h-4 w-4" />
              </Link>
              <a href="#how" className="btn-secondary px-5 py-3 text-base">
                See how it works
              </a>
            </div>

            <p className="mt-4 text-sm text-ink-muted">
              No account needed. Nothing is posted or shared.
            </p>
          </div>

          {/* Sample scorecard */}
          <div className="animate-fade-up lg:pl-6">
            <div className="card overflow-hidden shadow-lift">
              <div className="flex items-center gap-5 border-b border-line p-6">
                <ScoreRing score={5.3} />
                <div>
                  <p className="text-sm text-ink-muted">Overall</p>
                  <p className="text-lg font-semibold text-ink">
                    Promising, but needs work
                  </p>
                  <p className="mt-1 text-sm text-ink-soft">Instagram &middot; Ecommerce</p>
                </div>
              </div>
              <div className="grid gap-5 p-6 sm:grid-cols-2">
                {SAMPLE.map((s) => (
                  <ScoreMeter key={s.criterion} criterion={s.criterion} score={s.score} compact />
                ))}
              </div>
              <div className="border-t border-line bg-canvas p-6">
                <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
                  Top fix
                </p>
                <p className="mt-1.5 text-sm text-ink">
                  Replace the placeholder image with the product in use — there is no
                  focal point for the eye to land on.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="border-y border-line bg-canvas py-20">
        <div className="container-page">
          <h2 className="max-w-xl text-title font-semibold text-ink">
            Three steps, about ten seconds
          </h2>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {[
              {
                icon: icons.upload,
                title: "Upload your creative",
                body: "Drag in a PNG or JPG and say where it will run — the channel changes what good looks like.",
              },
              {
                icon: icons.target,
                title: "Get a scored critique",
                body: "Six things that decide whether an ad performs, each scored and explained in plain language.",
              },
              {
                icon: icons.check,
                title: "Fix and re-check",
                body: "Specific changes, not vague advice. Upload the new version and compare them side by side.",
              },
            ].map((step, i) => (
              <div key={step.title}>
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white text-brand-600 shadow-card">
                  <Icon path={step.icon} className="h-5 w-5" />
                </div>
                <p className="text-xs font-semibold text-brand-600">STEP {i + 1}</p>
                <h3 className="mt-1 text-lg font-semibold text-ink">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-soft">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* What gets scored */}
      <section id="scores" className="py-20">
        <div className="container-page">
          <h2 className="max-w-xl text-title font-semibold text-ink">
            Six things that decide whether an ad performs
          </h2>
          <p className="mt-4 max-w-2xl text-ink-soft">
            Every review scores the same six, so you can compare creatives fairly and
            watch them improve over time.
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {ALL_CRITERIA.map((c) => (
              <div key={c} className="card p-5">
                <h3 className="text-base font-semibold text-ink">
                  {CRITERION_COPY[c].label}
                </h3>
                <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">
                  {CRITERION_COPY[c].blurb}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Brand rules */}
      <section id="brand" className="border-t border-line bg-canvas py-20">
        <div className="container-page grid items-center gap-12 lg:grid-cols-2">
          <div>
            <h2 className="text-title font-semibold text-ink">
              It checks your brand rules too
            </h2>
            <p className="mt-4 text-ink-soft">
              Upload your brand guidelines once. After that, every review also checks
              tone of voice, colour rules, logo placement and claims you are not allowed
              to make — and tells you exactly which rule an ad breaks.
            </p>
            <ul className="mt-6 space-y-3">
              {[
                "Catches off-brand colour and missing logos",
                "Flags wording your guidelines rule out",
                "Quotes the specific rule, so you can check it yourself",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-ink">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-score-strong/10 text-score-strong-ink">
                    <Icon path={icons.check} className="h-3 w-3" />
                  </span>
                  {item}
                </li>
              ))}
            </ul>
            <Link to="/app/brands" className="btn-primary mt-8">
              Add your brand rules
            </Link>
          </div>

          <div className="card p-6 shadow-lift">
            <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
              Example findings
            </p>
            <div className="mt-4 space-y-4">
              <div className="rounded-xl border border-score-weak/25 bg-score-weak/[0.04] p-4">
                <p className="text-sm font-semibold text-score-weak-ink">
                  Off-brand call-to-action colour
                </p>
                <p className="mt-1 text-sm text-ink-soft">
                  The button uses a saturated blue. Your guidelines specify Dawn Coral or
                  Nimbus Slate.
                </p>
              </div>
              <div className="rounded-xl border border-score-weak/25 bg-score-weak/[0.04] p-4">
                <p className="text-sm font-semibold text-score-weak-ink">Logo missing</p>
                <p className="mt-1 text-sm text-ink-soft">
                  Your wordmark should sit in the lower-right corner. It is not present.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="py-20">
        <div className="container-page">
          <div className="rounded-xl2 bg-brand-600 px-8 py-14 text-center shadow-brand">
            <h2 className="text-title font-semibold text-white">
              Check your next ad before it runs
            </h2>
            <p className="mx-auto mt-4 max-w-md text-brand-100">
              One upload, one honest answer, about ten seconds.
            </p>
            <Link
              to="/app"
              className="btn mt-8 bg-white px-6 py-3 text-base text-brand-700 hover:bg-brand-50"
            >
              Check an ad
              <Icon path={icons.arrowRight} className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
