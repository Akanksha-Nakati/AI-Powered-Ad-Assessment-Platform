import { NavLink, Outlet } from "react-router-dom";
import { Icon, icons } from "../components/ui/Icon";
import { Logo } from "../components/ui/Logo";

const TABS = [
  { to: "/app", label: "Check an ad", icon: icons.spark, end: true },
  { to: "/app/compare", label: "Compare", icon: icons.layers },
  { to: "/app/history", label: "History", icon: icons.clock },
  { to: "/app/brands", label: "Brand rules", icon: icons.book },
];

export function AppLayout() {
  return (
    <div className="min-h-screen bg-canvas">
      <header className="sticky top-0 z-40 border-b border-line bg-white">
        <div className="container-page flex h-16 items-center justify-between gap-6">
          <Logo to="/" />
          <nav className="flex items-center gap-1 overflow-x-auto">
            {TABS.map((tab) => (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.end}
                // The label is hidden on small screens and the icon is
                // aria-hidden, so without this the tab announces nothing.
                aria-label={tab.label}
                className={({ isActive }) =>
                  "flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm transition " +
                  (isActive
                    ? "bg-brand-50 font-semibold text-brand-700"
                    : "text-ink-soft hover:bg-black/[0.04] hover:text-ink")
                }
              >
                <Icon path={tab.icon} className="h-4 w-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="container-page py-8 sm:py-10">
        <Outlet />
      </main>
    </div>
  );
}
