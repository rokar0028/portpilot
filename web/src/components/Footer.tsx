import Link from "next/link";

export function Footer() {
  return (
    <footer>
      <span>
        PORTPILOT <span className="footer-dot">·</span> BUILT FOR BETTER
        CONNECTIONS
      </span>
      <span>SPECIFICATIONS VERIFIED AGAINST MANUFACTURER SOURCES</span>
      <Link href="/coverage">Coverage &amp; limitations</Link>
    </footer>
  );
}
