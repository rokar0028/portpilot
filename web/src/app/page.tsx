"use client";

import { FormEvent, useState } from "react";

type Evidence = {
  title: string;
  url: string;
  excerpt: string;
  checked_on: string;
  status: string;
};
type Requirement = {
  name: string;
  detail: string;
  status: "passed" | "failed" | "unknown";
};
type Result = {
  verdict: string;
  summary: string;
  limits: string[];
  requirements: Requirement[];
  evidence: Evidence[];
  rule_engine_version: string;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const laptopId = "lenovo-ideapad-slim-3-14irh10r";
const accessoryId = "anker-364-usb-c-hub";

export default function Home() {
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API}/checks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          laptop_id: laptopId,
          accessory_id: accessoryId,
          setup: {
            external_displays: Number(form.get("displays")),
            resolution: String(form.get("resolution")),
            refresh_rate_hz: Number(form.get("refresh")),
            laptop_charging: form.get("charging") === "on",
          },
        }),
      });
      if (!response.ok)
        throw new Error(
          "The compatibility service could not complete this check.",
        );
      setResult(await response.json());
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not reach the PortPilot API. Start the backend and try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="#">
          <span className="brand-mark">P</span> portpilot
        </a>
        <span className="top-note">
          <span className="live-dot" /> Evidence first. No guessing.
        </span>
      </header>
      <section className="hero">
        <div className="eyebrow">
          <span>THE SETUP CHECKER</span>
          <span className="eyebrow-line" />
        </div>
        <h1>
          Will your gear
          <br />
          <em>work together?</em>
        </h1>
        <p className="intro">
          Pick a laptop, choose what you want to connect, and get a clear answer
          backed by manufacturer specifications.
        </p>
      </section>

      <section className="workspace">
        <form className="check-form" onSubmit={submit}>
          <div className="section-head">
            <div>
              <span className="step">01</span>
              <h2>Your devices</h2>
            </div>
            <span className="catalog-tag">STARTER CATALOGUE</span>
          </div>
          <label className="field-label" htmlFor="laptop">
            Laptop
          </label>
          <div className="select-wrap">
            <select id="laptop" defaultValue={laptopId}>
              <option value={laptopId}>Lenovo IdeaPad Slim 3 14IRH10R</option>
            </select>
            <span>⌄</span>
          </div>
          <div className="device-meta">
            <span className="device-icon laptop-icon">▱</span>
            <span>USB-C · DisplayPort 1.2 · USB PD 45–65 W</span>
            <span className="source-count">1 source ↗</span>
          </div>

          <div className="connector">
            <span />
            <span />
            <span />
          </div>

          <label className="field-label" htmlFor="accessory">
            Accessory
          </label>
          <div className="select-wrap">
            <select id="accessory" defaultValue={accessoryId}>
              <option value={accessoryId}>Anker 364 USB-C Hub</option>
            </select>
            <span>⌄</span>
          </div>
          <div className="device-meta">
            <span className="device-icon hub-icon">▦</span>
            <span>Dual HDMI · Up to 85 W pass-through</span>
            <span className="source-count">1 source ↗</span>
          </div>

          <div className="divider" />
          <div className="section-head compact">
            <div>
              <span className="step">02</span>
              <h2>Your setup</h2>
            </div>
          </div>
          <div className="setup-grid">
            <label>
              <span className="field-label">External displays</span>
              <div className="select-wrap">
                <select name="displays" defaultValue="1">
                  <option value="1">1 display</option>
                  <option value="2">2 displays</option>
                </select>
                <span>⌄</span>
              </div>
            </label>
            <label>
              <span className="field-label">Resolution</span>
              <div className="select-wrap">
                <select name="resolution" defaultValue="1920x1080">
                  <option value="1920x1080">1080p</option>
                  <option value="2560x1440">1440p</option>
                  <option value="3840x2160">4K UHD</option>
                </select>
                <span>⌄</span>
              </div>
            </label>
          </div>
          <div className="setup-bottom">
            <label className="check-option">
              <input type="checkbox" name="charging" defaultChecked />
              <span className="custom-check">✓</span>
              <span>Charge my laptop through the hub</span>
            </label>
            <label className="refresh">
              <span className="field-label">Refresh</span>
              <select name="refresh">
                <option value="60">60 Hz</option>
                <option value="30">30 Hz</option>
              </select>
            </label>
          </div>
          <button className="submit" type="submit" disabled={loading}>
            {loading ? (
              "Checking specifications…"
            ) : (
              <>
                Check my setup <span>→</span>
              </>
            )}
          </button>
          <p className="privacy-note">
            <span>✳</span> Checks use documented specs. If something can’t be
            verified, we’ll say so.
          </p>
        </form>

        <aside className="result-panel" aria-live="polite">
          {!result ? (
            <div className="empty-result">
              <div className="orbit">
                <span className="orbit-center">?</span>
                <i className="orbit-dot dot-a" />
                <i className="orbit-dot dot-b" />
                <i className="orbit-dot dot-c" />
              </div>
              <span className="result-kicker">YOUR RESULT</span>
              <h2>
                Clarity before
                <br />
                you connect.
              </h2>
              <p>
                Your compatibility report will show what works, what’s limited,
                and what the specs don’t tell us.
              </p>
              <div className="empty-legend">
                <span>
                  <i className="legend green" /> Supported
                </span>
                <span>
                  <i className="legend amber" /> Needs a check
                </span>
                <span>
                  <i className="legend red" /> Not supported
                </span>
              </div>
            </div>
          ) : (
            <div className="report">
              <div className="report-top">
                <span className="result-kicker">YOUR RESULT</span>
                <span className="version">
                  RULES {result.rule_engine_version}
                </span>
              </div>
              <div
                className={`verdict-icon ${result.verdict}`}
                aria-hidden="true"
              >
                {result.verdict === "compatible"
                  ? "✓"
                  : result.verdict === "incompatible"
                    ? "×"
                    : "?"}
              </div>
              <h2 className="verdict-title">
                {result.verdict === "compatible_with_limits"
                  ? "Works with limits"
                  : result.verdict.replaceAll("_", " ")}
              </h2>
              <p className="verdict-summary">{result.summary}</p>
              <div className="requirements">
                {result.requirements.map((item) => (
                  <div className="requirement" key={item.name}>
                    <span className={`status-icon ${item.status}`}>
                      {item.status === "passed"
                        ? "✓"
                        : item.status === "failed"
                          ? "×"
                          : "?"}
                    </span>
                    <div>
                      <strong>{item.name}</strong>
                      <p>{item.detail}</p>
                    </div>
                    <span className={`status-label ${item.status}`}>
                      {item.status === "unknown"
                        ? "UNVERIFIED"
                        : item.status.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
              <div className="evidence-head">
                <span>SPECIFICATION SOURCES</span>
                <span>{result.evidence.length} sources</span>
              </div>
              {result.evidence.map((item) => (
                <a
                  className="evidence-card"
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  key={item.url}
                >
                  <span className="evidence-check">↗</span>
                  <span>
                    <strong>{item.title}</strong>
                    <small>“{item.excerpt}”</small>
                  </span>
                </a>
              ))}
            </div>
          )}
        </aside>
      </section>
      {error && (
        <p className="error-banner" role="alert">
          {error}
        </p>
      )}
      <footer>
        <span>
          PORTPILOT <span className="footer-dot">·</span> BUILT FOR BETTER
          CONNECTIONS
        </span>
        <span>SPECIFICATIONS VERIFIED AGAINST MANUFACTURER SOURCES</span>
      </footer>
    </main>
  );
}
