import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet } from "react-router-dom";
import { api } from "../lib/api/client";
import { queryKeys } from "../lib/query";

const TABS = [
  { to: "/", label: "Assess", end: true },
  { to: "/compare", label: "Compare" },
  { to: "/history", label: "History" },
  { to: "/brands", label: "Brands" },
];

const PROVIDER_LABELS: Record<string, string> = {
  gemini: "Gemini",
  claude: "Claude",
};

function providerLabel(name: string | undefined) {
  return name ? (PROVIDER_LABELS[name] ?? name) : "…";
}

export function Layout() {
  // The badge used to hardcode "Gemini vision + Claude scoring", which was
  // wrong whenever SCORING_PROVIDER was set to gemini -- exactly the kind of
  // documentation drift this project already had once.
  const health = useQuery({ queryKey: queryKeys.health, queryFn: api.health });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      <div className="mx-auto max-w-6xl space-y-8 px-6 py-10">
        <header className="space-y-4 text-center">
          <div className="inline-flex items-center gap-3 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-1 text-sm text-cyan-100">
            RAG + {providerLabel(health.data?.vision_provider)} vision +{" "}
            {providerLabel(health.data?.scoring_provider)} scoring
          </div>
          <h1 className="text-4xl font-bold">AI-Powered Ad Assessment</h1>
          <p className="text-slate-300">
            Upload an ad, pick the channel, and get creative scores grounded in
            marketing guidance you can read.
          </p>
          <nav className="flex justify-center gap-1 pt-2">
            {TABS.map((tab) => (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  "rounded-xl px-4 py-2 text-sm transition " +
                  (isActive
                    ? "bg-white/10 font-semibold text-white"
                    : "text-slate-300 hover:bg-white/5")
                }
              >
                {tab.label}
              </NavLink>
            ))}
          </nav>
        </header>
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
