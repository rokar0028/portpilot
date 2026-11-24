import Link from "next/link";

export function TopBar() {
  return (
    <header className="topbar">
      <Link className="brand" href="/">
        <span className="brand-mark">P</span> portpilot
      </Link>
      <div className="top-actions">
        <Link className="coverage-nav" href="/coverage">
          Coverage &amp; limits
        </Link>
        <span className="top-note">
          <span className="live-dot" /> Evidence first. No guessing.
        </span>
      </div>
    </header>
  );
}
