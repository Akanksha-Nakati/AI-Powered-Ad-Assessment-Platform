import { FormEvent, useMemo, useState } from "react";
import { assessAd } from "./api";
import { AssessmentResponse, ScoreKeys } from "./types";
import { ScoreBar } from "./components/ScoreBar";
import { CitationList } from "./components/CitationList";

const scoreOrder: ScoreKeys[] = ["attention", "clarity", "targeting", "cta", "branding", "value"];

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [platform, setPlatform] = useState("Facebook/IG");
  const [industry, setIndustry] = useState("Ecommerce");
  const [adType, setAdType] = useState("Static Image");
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<AssessmentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const overallPct = useMemo(() => {
    if (!result?.overall_score) return 0;
    return Math.round((result.overall_score / 10) * 100);
  }, [result]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please upload an ad image.");
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const form = new FormData();
      form.append("ad_image", file);
      form.append("platform", platform);
      form.append("industry", industry);
      form.append("ad_type", adType);
      const data = await assessAd(form);
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Request failed. Check the API server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      <div className="mx-auto max-w-6xl px-6 py-10 space-y-8">
        <header className="space-y-3 text-center">
          <div className="inline-flex items-center gap-3 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-1 text-sm text-cyan-100">
            RAG + Gemini + Claude
          </div>
          <h1 className="text-4xl font-bold">AI-Powered Ad Assessment</h1>
          <p className="text-slate-300">
            Upload an ad, pick the channel, and get instant creative scores with grounded marketing guidance.
          </p>
        </header>

        <main className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section className="lg:col-span-1 card p-5 glass">
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="text-sm text-slate-200">Ad Image</label>
                <div className="mt-2 flex flex-col gap-3 rounded-2xl border border-dashed border-cyan-500/50 bg-cyan-500/5 p-4">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      setFile(f || null);
                      setPreview(f ? URL.createObjectURL(f) : null);
                    }}
                    className="text-sm text-slate-200"
                  />
                  {preview && (
                    <img
                      src={preview}
                      alt="preview"
                      className="h-48 w-full rounded-xl object-cover border border-cyan-500/40"
                    />
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3">
                <div className="space-y-1">
                  <label className="text-sm text-slate-200">Platform</label>
                  <select
                    value={platform}
                    onChange={(e) => setPlatform(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 focus:border-cyan-400 focus:outline-none"
                  >
                    {["Facebook/IG", "TikTok", "YouTube", "LinkedIn", "Display"].map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-sm text-slate-200">Industry</label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 focus:border-cyan-400 focus:outline-none"
                  >
                    {["Ecommerce", "SaaS", "Finance", "Health/Wellness", "Education"].map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-sm text-slate-200">Ad Type</label>
                  <select
                    value={adType}
                    onChange={(e) => setAdType(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 focus:border-cyan-400 focus:outline-none"
                  >
                    {["Static Image", "Carousel", "Story/Reel", "Banner"].map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-gradient-to-r from-cyan-500 via-blue-500 to-violet-600 px-4 py-3 text-center font-semibold shadow-lg shadow-cyan-500/20 transition hover:opacity-90 disabled:opacity-60"
              >
                {loading ? "Analyzing..." : "Assess Ad"}
              </button>
              {error && <p className="text-sm text-red-300">{error}</p>}
            </form>
          </section>

          <section className="lg:col-span-2 space-y-4">
            {!result && (
              <div className="card glass p-6 text-slate-300">
                Submit an ad to see creative scores, feedback, and citations from the marketing knowledge base.
              </div>
            )}

            {result && (
              <>
                <div className="card glass p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-300">Overall score</p>
                      <h2 className="text-3xl font-bold text-white">{result.overall_score?.toFixed(1) ?? "-"}/10</h2>
                    </div>
                    <div className="relative h-28 w-28">
                      <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
                        <path
                          d="M18 2.0845
                             a 15.9155 15.9155 0 0 1 0 31.831
                             a 15.9155 15.9155 0 0 1 0 -31.831"
                          fill="none"
                          stroke="#1e293b"
                          strokeWidth="3"
                        />
                        <path
                          d="M18 2.0845
                             a 15.9155 15.9155 0 0 1 0 31.831"
                          fill="none"
                          stroke="url(#grad)"
                          strokeWidth="3"
                          strokeDasharray={`${overallPct}, 100`}
                        />
                        <defs>
                          <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#22d3ee" />
                            <stop offset="50%" stopColor="#6366f1" />
                            <stop offset="100%" stopColor="#a855f7" />
                          </linearGradient>
                        </defs>
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center text-lg font-semibold">
                        {overallPct}%
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    {scoreOrder.map((key) => (
                      <ScoreBar key={key} label={key} value={result.scores[key]} />
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <div className="card glass p-5 space-y-3">
                    <h3 className="text-lg font-semibold text-white">Feedback</h3>
                    <p className="text-sm text-slate-200">{result.feedback}</p>
                  </div>
                  <div className="card glass p-5 space-y-3">
                    <h3 className="text-lg font-semibold text-white">Recommendations</h3>
                    <ul className="space-y-2 text-sm text-slate-200">
                      {result.recommendations.map((rec, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-cyan-300">•</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                      {result.recommendations.length === 0 && (
                        <li className="text-slate-400">No recommendations returned.</li>
                      )}
                    </ul>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <div className="card glass p-5 space-y-3">
                    <h3 className="text-lg font-semibold text-white">Gemini Image Analysis</h3>
                    <pre className="whitespace-pre-wrap text-xs text-slate-200">
                      {JSON.stringify(result.gemini, null, 2)}
                    </pre>
                  </div>
                  <CitationList citations={result.citations} context={result.context} />
                </div>
              </>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;

