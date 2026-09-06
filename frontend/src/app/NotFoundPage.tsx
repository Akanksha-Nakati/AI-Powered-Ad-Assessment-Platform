import { Link } from "react-router-dom";
import { Logo } from "../components/ui/Logo";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-canvas px-6 text-center">
      <Logo />
      <h1 className="mt-8 text-title font-semibold text-ink">Page not found</h1>
      <p className="mt-3 max-w-sm text-ink-soft">
        That link doesn't lead anywhere. Let's get you back to checking ads.
      </p>
      <Link to="/app" className="btn-primary mt-8">
        Check an ad
      </Link>
    </div>
  );
}
