"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";

type Evidence = {
  id: string;
  capability_key: string;
  title: string;
  url: string;
  excerpt: string;
  checked_on: string;
  status: string;
};
type Laptop = {
  id: string;
  name: string;
  model_code: string | null;
  usb_c_video_supported: boolean | null;
  usb_c_data_rate_gbps: number | null;
  usb_c_dp_version: string | null;
  usb_c_pd_input_min_w: number | null;
  usb_c_pd_input_max_w: number | null;
  evidence: Evidence[];
};
type Accessory = {
  id: string;
  name: string;
  model_code: string | null;
  category: string;
  host_connection: string | null;
  requires_usb_c_dp_alt_mode: boolean | null;
  hdmi_port_count: number | null;
  hdmi_max_resolution: string | null;
  hdmi_max_refresh_hz: number | null;
  pd_pass_through_max_w: number | null;
  usb_c_output_max_w: number | null;
  evidence: Evidence[];
};
type Catalog = { laptops: Laptop[]; accessories: Accessory[] };
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
type Setup = {
  external_displays: number;
  resolution: string;
  refresh_rate_hz: number;
  laptop_charging: boolean;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const defaultLaptopId = "lenovo-ideapad-slim-3-14irh10r";
const defaultAccessoryId = "anker-364-usb-c-hub";

export default function Home() {
  const checkRequestVersion = useRef(0);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [laptopId, setLaptopId] = useState("");
  const [accessoryId, setAccessoryId] = useState("");
  const [setup, setSetup] = useState<Setup>({
    external_displays: 1,
    resolution: "1920x1080",
    refresh_rate_hz: 60,
    laptop_charging: true,
  });
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [shareMessage, setShareMessage] = useState("");

  function updateLaptopId(value: string) {
    checkRequestVersion.current += 1;
    setLoading(false);
    setLaptopId(value);
    setResult(null);
    setError("");
  }

  function updateAccessoryId(value: string) {
    checkRequestVersion.current += 1;
    setLoading(false);
    setAccessoryId(value);
    setResult(null);
    setError("");
  }

  function updateSetup(nextSetup: Setup) {
    checkRequestVersion.current += 1;
    setLoading(false);
    setSetup(nextSetup);
    setResult(null);
    setError("");
  }

  async function runCheck(
    nextLaptopId: string,
    nextAccessoryId: string,
    nextSetup: Setup,
  ): Promise<boolean> {
    const requestVersion = ++checkRequestVersion.current;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch(`${API}/checks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          laptop_id: nextLaptopId,
          accessory_id: nextAccessoryId,
          setup: nextSetup,
        }),
      });
      if (!response.ok)
        throw new Error(
          "The compatibility service could not complete this check.",
        );
      const nextResult = (await response.json()) as Result;
      if (requestVersion !== checkRequestVersion.current) return false;
      setResult(nextResult);
      const url = new URL(window.location.href);
      url.search = new URLSearchParams({
        laptop: nextLaptopId,
        accessory: nextAccessoryId,
        displays: String(nextSetup.external_displays),
        resolution: nextSetup.resolution,
        refresh: String(nextSetup.refresh_rate_hz),
        charging: String(nextSetup.laptop_charging),
      }).toString();
      window.history.replaceState({}, "", url);
      return true;
    } catch (cause) {
      if (requestVersion !== checkRequestVersion.current) return false;
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not reach the PortPilot API. Start the backend and try again.",
      );
      return false;
    } finally {
      if (requestVersion === checkRequestVersion.current) setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    async function loadCatalog() {
      try {
        const response = await fetch(`${API}/devices`);
        if (!response.ok)
          throw new Error("The device catalogue could not be loaded.");
        const data: Catalog = await response.json();
        if (active) {
          const params = new URLSearchParams(window.location.search);
          const sharedLaptop = params.get("laptop");
          const sharedAccessory = params.get("accessory");
          const nextLaptop = data.laptops.some(
            (item) => item.id === sharedLaptop,
          )
            ? sharedLaptop!
            : data.laptops.some((item) => item.id === defaultLaptopId)
              ? defaultLaptopId
              : (data.laptops[0]?.id ?? "");
          const nextAccessory = data.accessories.some(
            (item) => item.id === sharedAccessory,
          )
            ? sharedAccessory!
            : data.accessories.some((item) => item.id === defaultAccessoryId)
              ? defaultAccessoryId
              : (data.accessories[0]?.id ?? "");
          const requestedDisplays = Number(params.get("displays"));
          const requestedRefresh = Number(params.get("refresh"));
          const nextSetup: Setup = {
            external_displays: [1, 2].includes(requestedDisplays)
              ? requestedDisplays
              : 1,
            resolution: ["1920x1080", "2560x1440", "3840x2160"].includes(
              params.get("resolution") ?? "",
            )
              ? params.get("resolution")!
              : "1920x1080",
            refresh_rate_hz: [30, 60].includes(requestedRefresh)
              ? requestedRefresh
              : 60,
            laptop_charging: params.has("charging")
              ? params.get("charging") === "true"
              : true,
          };
          setCatalog(data);
          setLaptopId(nextLaptop);
          setAccessoryId(nextAccessory);
          setSetup(nextSetup);
          if (
            sharedLaptop &&
            sharedAccessory &&
            nextLaptop === sharedLaptop &&
            nextAccessory === sharedAccessory
          ) {
            void runCheck(nextLaptop, nextAccessory, nextSetup);
          }
        }
      } catch (cause) {
        if (active) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Could not reach the PortPilot API. Start the backend and try again.",
          );
        }
      }
    }
    void loadCatalog();
    return () => {
      active = false;
    };
  }, []);

  const selectedLaptop = catalog?.laptops.find((item) => item.id === laptopId);
  const selectedAccessory = catalog?.accessories.find(
    (item) => item.id === accessoryId,
  );

  function sourceCount(evidence: Evidence[]) {
    return new Set(evidence.map((source) => source.url)).size;
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runCheck(laptopId, accessoryId, setup);
  }

  async function copyShareLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setShareMessage("Link copied");
    } catch {
      setShareMessage("Copy the link from your address bar");
    }
    window.setTimeout(() => setShareMessage(""), 2600);
  }

  return (
    <main className="shell">
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
            <select
              id="laptop"
              name="laptop_id"
              value={laptopId}
              onChange={(event) => updateLaptopId(event.target.value)}
              disabled={!catalog}
            >
              {catalog?.laptops.map((laptop) => (
                <option value={laptop.id} key={laptop.id}>
                  {laptop.name}
                </option>
              ))}
            </select>
            <span>⌄</span>
          </div>
          <div className="device-meta">
            <span className="device-icon laptop-icon">▱</span>
            <span>
              {selectedLaptop
                ? `${selectedLaptop.model_code ?? selectedLaptop.id} · ${selectedLaptop.usb_c_video_supported === true ? `USB-C video, DP ${selectedLaptop.usb_c_dp_version ?? "version unknown"}` : selectedLaptop.usb_c_video_supported === false ? "USB-C video not supported" : "USB-C video unverified"} · PD ${selectedLaptop.usb_c_pd_input_min_w ?? "?"}–${selectedLaptop.usb_c_pd_input_max_w ?? "?"} W`
                : "Loading laptop specifications…"}
            </span>
            {selectedLaptop?.evidence[0] && (
              <a
                className="source-count"
                href={selectedLaptop.evidence[0].url}
                title={selectedLaptop.evidence[0].title}
                target="_blank"
                rel="noreferrer"
              >
                {sourceCount(selectedLaptop.evidence)} source
                {sourceCount(selectedLaptop.evidence) === 1 ? "" : "s"} ↗
              </a>
            )}
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
            <select
              id="accessory"
              name="accessory_id"
              value={accessoryId}
              onChange={(event) => updateAccessoryId(event.target.value)}
              disabled={!catalog}
            >
              {catalog?.accessories.map((accessory) => (
                <option value={accessory.id} key={accessory.id}>
                  {accessory.name}
                </option>
              ))}
            </select>
            <span>⌄</span>
          </div>
          <div className="device-meta">
            <span className="device-icon hub-icon">▦</span>
            <span>
              {selectedAccessory
                ? `${selectedAccessory.model_code ?? selectedAccessory.id} · ${selectedAccessory.category === "usb_c_charger" ? `USB-C charger · ${selectedAccessory.usb_c_output_max_w ?? "?"} W output` : `${selectedAccessory.hdmi_port_count ?? "?"} HDMI · ${selectedAccessory.hdmi_max_resolution ?? "?"} · ${selectedAccessory.requires_usb_c_dp_alt_mode === true ? "DP Alt Mode required" : "host video requirement unknown"}`}`
                : "Loading accessory specifications…"}
            </span>
            {selectedAccessory?.evidence[0] && (
              <a
                className="source-count"
                href={selectedAccessory.evidence[0].url}
                title={selectedAccessory.evidence[0].title}
                target="_blank"
                rel="noreferrer"
              >
                {sourceCount(selectedAccessory.evidence)} source
                {sourceCount(selectedAccessory.evidence) === 1 ? "" : "s"} ↗
              </a>
            )}
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
                <select
                  name="displays"
                  value={setup.external_displays}
                  onChange={(event) =>
                    updateSetup({
                      ...setup,
                      external_displays: Number(event.target.value),
                    })
                  }
                >
                  <option value="1">1 display</option>
                  <option value="2">2 displays</option>
                </select>
                <span>⌄</span>
              </div>
            </label>
            <label>
              <span className="field-label">Resolution</span>
              <div className="select-wrap">
                <select
                  name="resolution"
                  value={setup.resolution}
                  onChange={(event) =>
                    updateSetup({ ...setup, resolution: event.target.value })
                  }
                >
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
              <input
                type="checkbox"
                name="charging"
                checked={setup.laptop_charging}
                onChange={(event) =>
                  updateSetup({ ...setup, laptop_charging: event.target.checked })
                }
              />
              <span className="custom-check">✓</span>
              <span>Charge my laptop through this accessory</span>
            </label>
            <label className="refresh">
              <span className="field-label">Refresh</span>
              <select
                name="refresh"
                value={setup.refresh_rate_hz}
                onChange={(event) =>
                  updateSetup({
                    ...setup,
                    refresh_rate_hz: Number(event.target.value),
                  })
                }
              >
                <option value="60">60 Hz</option>
                <option value="30">30 Hz</option>
              </select>
            </label>
          </div>
          <button
            className="submit"
            type="submit"
            disabled={
              loading ||
              !catalog ||
              !catalog.laptops.length ||
              !catalog.accessories.length ||
              !laptopId ||
              !accessoryId
            }
          >
            {loading ? (
              "Checking specifications…"
            ) : !catalog ? (
              "Loading catalogue…"
            ) : !catalog.laptops.length || !catalog.accessories.length ? (
              "Catalogue unavailable"
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
              <div className="device-pair">
                <span>{selectedLaptop?.name ?? laptopId}</span>
                <span aria-hidden="true">→</span>
                <span>{selectedAccessory?.name ?? accessoryId}</span>
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
              <button
                className="share-button"
                type="button"
                onClick={copyShareLink}
              >
                Share this result <span aria-hidden="true">↗</span>
              </button>
              {shareMessage && (
                <span className="share-message" role="status">
                  {shareMessage}
                </span>
              )}
              {result.limits.length > 0 && (
                <ul className="limit-list" aria-label="Known limitations">
                  {result.limits.map((limit) => (
                    <li key={limit}>{limit}</li>
                  ))}
                </ul>
              )}
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
                <span>
                  {sourceCount(result.evidence)} sources ·{" "}
                  {result.evidence.length} capability records
                </span>
              </div>
              {result.evidence.map((item) => (
                <a
                  className="evidence-card"
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  key={item.id}
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
      <section className="glossary" aria-labelledby="glossary-title">
        <div>
          <span className="eyebrow">QUICK REFERENCE</span>
          <h2 id="glossary-title">A few useful terms</h2>
        </div>
        <details>
          <summary>USB-C</summary>
          <p>
            The connector shape. By itself, USB-C does not guarantee video
            output, charging, or a particular data speed.
          </p>
        </details>
        <details>
          <summary>DisplayPort Alt Mode</summary>
          <p>
            A way for a USB-C port to carry DisplayPort video to a display or
            hub.
          </p>
        </details>
        <details>
          <summary>USB Power Delivery</summary>
          <p>
            A charging standard that negotiates power between a charger and a
            device. The available wattage depends on both sides.
          </p>
        </details>
        <details>
          <summary>USB4</summary>
          <p>
            A USB connection standard with higher data capabilities; the exact
            features still depend on the laptop port and device.
          </p>
        </details>
        <details>
          <summary>Thunderbolt</summary>
          <p>
            A high-speed connection standard that can carry data, video, and
            power. Check the exact port and device specifications.
          </p>
        </details>
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
        <a href="/coverage">Coverage &amp; limitations</a>
      </footer>
    </main>
  );
}
