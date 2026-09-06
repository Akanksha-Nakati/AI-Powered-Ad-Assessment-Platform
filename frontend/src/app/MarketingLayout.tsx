import { Link, Outlet } from "react-router-dom";
import { Logo } from "../components/ui/Logo";

export function MarketingLayout() {
  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-40 border-b border-line/70 bg-white/85 backdrop-blur">
        <div className="container-page flex h-16 items-center justify-between">
          <Logo />
          <nav className="hidden items-center gap-7 text-sm text-ink-soft md:flex">
            <a href="#how" className="hover:text-ink">How it works</a>
            <a href="#scores" className="hover:text-ink">What you get</a>
            <a href="#brand" className="hover:text-ink">Brand rules</a>
          </nav>
          <Link to="/app" className="btn-primary">Check an ad</Link>
        </div>
      </header>

      <Outlet />

      <footer className="border-t border-line bg-canvas">
        <div className="container-page flex flex-col items-center justify-between gap-4 py-10 sm:flex-row">
          <Logo />
          <p className="text-sm text-ink-muted">
            Feedback on ad creative, before you spend on it.
          </p>
        </div>
      </footer>
    </div>
  );
}
