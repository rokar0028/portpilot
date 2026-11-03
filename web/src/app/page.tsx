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
  external_displays: number | null;
  resolution: string | null;
  refresh_rate_hz: number | null;
  laptop_charging: boolean | null;
};
type ParsedSetup = {
  setup: Setup;
  needs_clarification: boolean;
  clarification_questions: string[];
  unsupported_requests: string[];
  notice: string;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const exampleLaptopId = "lenovo-ideapad-slim-3-14irh10r";
const exampleAccessoryId = "anker-nano-hub-7in1-a83d2";
const exampleSetup: Setup = {
  external_displays: 1,
  resolution: "1920x1080",
  refresh_rate_hz: 60,
  laptop_charging: true,
};

export default function Home() {
  const checkRequestVersion = useRef(0);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogAttempt, setCatalogAttempt] = useState(0);
  const [catalogError, setCatalogError] = useState(false);
  const [laptopId, setLaptopId] = useState("");
  const [accessoryId, setAccessoryId] = useState("");
  const [setup, setSetup] = useState<Setup>({
    external_displays: 1,
    resolution: "1920x1080",
    refresh_rate_hz: 60,
    laptop_charging: true,
  });
  const [setupDescription, setSetupDescription] = useState("");
  const [parsedSetup, setParsedSetup] = useState<ParsedSetup | null>(null);
  const [parsedSetupReviewed, setParsedSetupReviewed] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [shareMessage, setShareMessage] = useState("");
  const [reportNote, setReportNote] = useState("");
  const [reportMessage, setReportMessage] = useState("");
  const [reporting, setReporting] = useState(false);

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
    if (parsedSetup) setParsedSetupReviewed(false);
    setResult(null);
    setError("");
  }

  async function parseDescription() {
    setParsing(true);
    setError("");
    try {
      const response = await fetch(`${API}/setup-requests/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: setupDescription }),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(
          data.detail?.message ?? "Setup parsing is unavailable.",
        );
      const parsed = data as ParsedSetup;
      setSetup(parsed.setup);
      setParsedSetup(parsed);
      setParsedSetupReviewed(false);
    } catch (cause) {
      setError(
        cause instanceof TypeError
          ? "We couldn’t reach PortPilot. Check that the API is running, then try again."
          : cause instanceof Error
            ? cause.message
            : "Setup interpretation is unavailable. You can still set the fields manually.",
      );
    } finally {
      setParsing(false);
    }
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
    setReportMessage("");
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
        resolution: String(nextSetup.resolution),
        refresh: String(nextSetup.refresh_rate_hz),
        charging: String(nextSetup.laptop_charging),
      }).toString();
      window.history.replaceState({}, "", url);
      return true;
    } catch (cause) {
      if (requestVersion !== checkRequestVersion.current) return false;
      setError(
        cause instanceof TypeError
          ? "We couldn’t reach PortPilot. Check that the API is running, then try again."
          : cause instanceof Error
            ? cause.message
            : "We couldn’t complete the check. Please try again.",
      );
      return false;
    } finally {
      if (requestVersion === checkRequestVersion.current) setLoading(false);
    }
  }

  async function tryExample() {
    if (
      !catalog ||
      !catalog.laptops.some((item) => item.id === exampleLaptopId) ||
      !catalog.accessories.some((item) => item.id === exampleAccessoryId)
    ) {
      setError("The sample check is not available in the current catalogue.");
      return;
    }

    setLaptopId(exampleLaptopId);
    setAccessoryId(exampleAccessoryId);
    setSetup(exampleSetup);
    setSetupDescription("");
    setParsedSetup(null);
    setParsedSetupReviewed(false);
    const checked = await runCheck(
      exampleLaptopId,
      exampleAccessoryId,
      exampleSetup,
    );
    if (checked && window.matchMedia("(max-width: 800px)").matches) {
      document.getElementById("result-panel")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }

  useEffect(() => {
    let active = true;
    async function loadCatalog() {
      setCatalogLoading(true);
      setCatalogError(false);
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
            : "";
          const nextAccessory = data.accessories.some(
            (item) => item.id === sharedAccessory,
          )
            ? sharedAccessory!
            : "";
          const rawDisplays = params.get("displays");
          const rawRefresh = params.get("refresh");
          const rawResolution = params.get("resolution");
          const rawCharging = params.get("charging");

          const parsedDisplays =
            rawDisplays !== null &&
            rawDisplays !== "" &&
            !isNaN(Number(rawDisplays))
              ? Number(rawDisplays)
              : null;
          const parsedRefresh =
            rawRefresh !== null &&
            rawRefresh !== "" &&
            !isNaN(Number(rawRefresh))
              ? Number(rawRefresh)
              : null;

          const nextSetup: Setup = {
            external_displays:
              parsedDisplays !== null &&
              [0, 1, 2, 3, 4].includes(parsedDisplays)
                ? parsedDisplays
                : 1,
            resolution:
              rawResolution &&
              rawResolution !== "null" &&
              rawResolution.length <= 30
                ? rawResolution
                : "1920x1080",
            refresh_rate_hz:
              parsedRefresh !== null &&
              parsedRefresh >= 24 &&
              parsedRefresh <= 240
                ? parsedRefresh
                : 60,
            laptop_charging:
              rawCharging === "true"
                ? true
                : rawCharging === "false"
                  ? false
                  : rawCharging === "null" || rawCharging === ""
                    ? null
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
      } catch {
        if (active) {
          setCatalogError(true);
        }
      } finally {
        if (active) setCatalogLoading(false);
      }
    }
    void loadCatalog();
    return () => {
      active = false;
    };
  }, [catalogAttempt]);

  const selectedLaptop = catalog?.laptops.find((item) => item.id === laptopId);
  const selectedAccessory = catalog?.accessories.find(
    (item) => item.id === accessoryId,
  );
  const resultHeading = result
    ? result.verdict === "compatible"
      ? "Looks compatible"
      : result.verdict === "compatible_with_limits"
        ? "Works with limits"
        : result.verdict === "incompatible"
          ? "Doesn’t meet this setup"
          : "Not enough information"
    : "";
  const announcement = loading
    ? "Checking your setup. Comparing your devices with their published specifications."
    : parsing
      ? "Interpreting your setup description."
      : parsedSetup && !parsedSetupReviewed
        ? "Setup interpreted. Review the extracted requirements and confirm them before checking."
        : result
          ? `Check complete. ${resultHeading}. ${result.summary}`
          : "";

  function sourceCount(evidence: Evidence[]) {
    return new Set(evidence.map((source) => source.url)).size;
  }

  async function submitResultReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!result) return;
    setReporting(true);
    setReportMessage("");
    try {
      const response = await fetch(`${API}/result-reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          laptop_id: laptopId,
          accessory_id: accessoryId,
          setup,
          verdict: result.verdict,
          rule_engine_version: result.rule_engine_version,
          note: reportNote,
        }),
      });
      if (!response.ok)
        throw new Error("Report could not be sent. Please try again.");
      setReportMessage("Thanks. Your report was sent to the PortPilot team.");
      setReportNote("");
    } catch (cause) {
      setReportMessage(
        cause instanceof Error ? cause.message : "Report could not be sent.",
      );
    } finally {
      setReporting(false);
    }
  }

  function groupEvidence(evidence: Evidence[]) {
    return Array.from(
      evidence.reduce((groups, item) => {
        const group = groups.get(item.url) ?? [];
        group.push(item);
        groups.set(item.url, group);
        return groups;
      }, new Map<string, Evidence[]>()),
    );
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
          Will your devices
          <br />
          <em>work together?</em>
        </h1>
        <p className="intro">
          Choose the laptop you have and the dock, hub or charger you want to
          connect. We’ll check their published specs against your screen and
          charging needs.
        </p>
        <div className="hero-actions">
          <span>
            New here? Try a sample report, or choose your own devices below.
          </span>
          <button
            className="sample-link"
            type="button"
            onClick={() => void tryExample()}
            disabled={!catalog || loading}
          >
            Try a sample report <span aria-hidden="true">→</span>
          </button>
        </div>
        <p className="sample-detail">
          IdeaPad Slim 3 14IRH10R + Anker Nano Hub A83D2 · one 1080p display and
          laptop charging.
        </p>
      </section>

      <section className="workspace">
        <form className="check-form" onSubmit={submit}>
          <div className="section-head">
            <div>
              <span className="step">01</span>
              <h2>Your devices</h2>
            </div>
            <span className="catalog-tag">VERIFIED MODELS</span>
          </div>
          <label className="field-label" htmlFor="laptop">
            Your laptop
          </label>
          <div className="select-wrap">
            <select
              id="laptop"
              name="laptop_id"
              value={laptopId}
              onChange={(event) => updateLaptopId(event.target.value)}
              disabled={!catalog}
            >
              <option value="">Choose your exact laptop model</option>
              {catalog?.laptops.map((laptop) => (
                <option value={laptop.id} key={laptop.id}>
                  {laptop.name}
                  {laptop.model_code ? ` · ${laptop.model_code}` : ""}
                </option>
              ))}
            </select>
            <span>⌄</span>
          </div>
          <div className="device-meta">
            <span className="device-icon laptop-icon">▱</span>
            <span>
              {selectedLaptop
                ? `Selected model code: ${selectedLaptop.model_code ?? selectedLaptop.id}`
                : catalogLoading
                  ? "Loading laptop details…"
                  : catalogError
                    ? "Device list unavailable. Retry below."
                    : "Choose the exact model; similar names can have different ports."}
            </span>
          </div>
          {selectedLaptop && (
            <details className="device-facts">
              <summary>See verified details</summary>
              <p>
                USB-C display output:{" "}
                {selectedLaptop.usb_c_video_supported === true
                  ? `supported${selectedLaptop.usb_c_dp_version ? ` (DisplayPort ${selectedLaptop.usb_c_dp_version})` : ""}`
                  : selectedLaptop.usb_c_video_supported === false
                    ? "not supported"
                    : "not documented"}
                <br />
                USB-C charging:{" "}
                {selectedLaptop.usb_c_pd_input_max_w
                  ? `up to ${selectedLaptop.usb_c_pd_input_max_w} W`
                  : "not documented"}
              </p>
              {groupEvidence(selectedLaptop.evidence).map(([url, records]) => (
                <a
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  key={records[0].id}
                >
                  {records[0].title} ↗
                </a>
              ))}
            </details>
          )}
          <p className="catalog-help">
            Can’t find your exact model?{" "}
            <Link href="/coverage#supported-devices">
              See supported devices and model-code tips.
            </Link>
          </p>
          <details className="model-help">
            <summary>Where can I find my exact laptop model?</summary>
            <p>
              Check the label on the underside or inside the battery/service
              compartment, or the original box. Look for “Model”, “Product”, or
              “MTM”; serial numbers are not needed.
            </p>
            <ul>
              <li>
                <strong>Windows:</strong> Settings → System → About, or run{" "}
                <code>msinfo32</code> and read System Model.
              </li>
              <li>
                <strong>macOS:</strong> Apple menu → About This Mac. For a model
                identifier, open System Information → Hardware.
              </li>
              <li>
                <strong>ChromeOS:</strong> Settings → About ChromeOS →
                Diagnostics, or check the label on the device.
              </li>
            </ul>
            <p>
              Match the full model code on the manufacturer support page. Don’t
              share a serial number.
            </p>
          </details>

          <div className="connector">
            <span />
            <span />
            <span />
          </div>

          <label className="field-label" htmlFor="accessory">
            Connect a dock, hub or charger
          </label>
          <div className="select-wrap">
            <select
              id="accessory"
              name="accessory_id"
              value={accessoryId}
              onChange={(event) => updateAccessoryId(event.target.value)}
              disabled={!catalog}
            >
              <option value="">Choose the exact model</option>
              {catalog?.accessories.map((accessory) => (
                <option value={accessory.id} key={accessory.id}>
                  {accessory.name}
                  {accessory.model_code ? ` · ${accessory.model_code}` : ""}
                </option>
              ))}
            </select>
            <span>⌄</span>
          </div>
          <div className="device-meta">
            <span className="device-icon hub-icon">▦</span>
            <span>
              {selectedAccessory
                ? `Selected model code: ${selectedAccessory.model_code ?? selectedAccessory.id}`
                : catalogLoading
                  ? "Loading accessory details…"
                  : catalogError
                    ? "Device list unavailable. Retry below."
                    : "Choose the exact accessory model to check its documented features."}
            </span>
          </div>
          {selectedAccessory && (
            <details className="device-facts">
              <summary>See verified details</summary>
              <p>
                {selectedAccessory.category === "usb_c_charger"
                  ? `USB-C charging output: ${selectedAccessory.usb_c_output_max_w ? `up to ${selectedAccessory.usb_c_output_max_w} W` : "not documented"}`
                  : `Display outputs: ${selectedAccessory.hdmi_port_count ?? "not documented"} HDMI · up to ${selectedAccessory.hdmi_max_resolution ?? "not documented"}${selectedAccessory.hdmi_max_refresh_hz ? ` at ${selectedAccessory.hdmi_max_refresh_hz} Hz` : ""}`}
                {selectedAccessory.category !== "usb_c_charger" && (
                  <>
                    <br />
                    Laptop must support USB-C video:{" "}
                    {selectedAccessory.requires_usb_c_dp_alt_mode === true
                      ? "yes"
                      : selectedAccessory.requires_usb_c_dp_alt_mode === false
                        ? "no"
                        : "not documented"}
                  </>
                )}
              </p>
              {groupEvidence(selectedAccessory.evidence).map(
                ([url, records]) => (
                  <a
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    key={records[0].id}
                  >
                    {records[0].title} ↗
                  </a>
                ),
              )}
            </details>
          )}
          <p className="catalog-help">
            Not sure which version you have? Check its product code on the label
            or manufacturer page; don’t choose a similar-looking model.
          </p>

          <div className="divider" />
          <div className="section-head compact">
            <div>
              <span className="step">02</span>
              <h2>Screen &amp; charging</h2>
            </div>
          </div>
          <p className="setup-default-note">
            By default, we’ll check one 1080p screen at 60 Hz and laptop
            charging. Adjust these if your setup is different.
          </p>
          <details className="advanced-setup">
            <summary>Adjust screen or charging needs</summary>
            <div className="advanced-setup-content">
              <div className="setup-parser">
                <label className="field-label" htmlFor="setup-description">
                  Describe your setup (optional)
                </label>
                <textarea
                  id="setup-description"
                  value={setupDescription}
                  onChange={(event) => setSetupDescription(event.target.value)}
                  maxLength={1000}
                  placeholder="For example: one 4K display at 60 Hz and laptop charging"
                  rows={3}
                />
                <p className="parser-privacy">
                  Only this description is sent to the configured parsing
                  provider. Don’t include personal information.
                </p>
                <button
                  className="parse-button"
                  type="button"
                  onClick={() => void parseDescription()}
                  disabled={parsing || setupDescription.trim().length < 3}
                >
                  {parsing ? "Interpreting setup…" : "Interpret setup"}
                </button>
                {parsedSetup && (
                  <div className="parse-review">
                    <strong>
                      Review these extracted fields and correct them below.
                    </strong>
                    <p>{parsedSetup.notice}</p>
                    {parsedSetup.needs_clarification && (
                      <p>
                        Needs clarification:{" "}
                        {parsedSetup.clarification_questions.join(" ")}
                      </p>
                    )}
                    {parsedSetup.unsupported_requests.length > 0 && (
                      <p>
                        Not checked:{" "}
                        {parsedSetup.unsupported_requests.join("; ")}
                      </p>
                    )}
                    {Object.entries(parsedSetup.setup).some(
                      ([, value]) => value === null,
                    ) && (
                      <p>
                        Some fields are unknown. Fill in any requirement you
                        want checked.
                      </p>
                    )}
                    <label className="review-confirm">
                      <input
                        type="checkbox"
                        checked={parsedSetupReviewed}
                        onChange={(event) =>
                          setParsedSetupReviewed(event.target.checked)
                        }
                      />
                      I reviewed these requirements
                    </label>
                  </div>
                )}
              </div>
              <div className="setup-grid">
                <label>
                  <span className="field-label">External screens</span>
                  <div className="select-wrap">
                    <select
                      name="displays"
                      value={setup.external_displays ?? ""}
                      onChange={(event) =>
                        updateSetup({
                          ...setup,
                          external_displays: event.target.value
                            ? Number(event.target.value)
                            : null,
                        })
                      }
                    >
                      <option value="" disabled>
                        Choose display count
                      </option>
                      {[0, 1, 2, 3, 4].map((count) => (
                        <option value={count} key={count}>
                          {count} display{count === 1 ? "" : "s"}
                        </option>
                      ))}
                    </select>
                    <span>⌄</span>
                  </div>
                </label>
                <label>
                  <span className="field-label">Resolution</span>
                  <div className="select-wrap">
                    <select
                      name="resolution"
                      value={setup.resolution ?? ""}
                      onChange={(event) =>
                        updateSetup({
                          ...setup,
                          resolution: event.target.value || null,
                        })
                      }
                    >
                      <option value="" disabled>
                        Choose resolution
                      </option>
                      {setup.resolution &&
                        !["1920x1080", "2560x1440", "3840x2160"].includes(
                          setup.resolution,
                        ) && (
                          <option value={setup.resolution}>
                            {setup.resolution}
                          </option>
                        )}
                      <option value="1920x1080">1080p</option>
                      <option value="2560x1440">1440p</option>
                      <option value="3840x2160">4K UHD</option>
                    </select>
                    <span>⌄</span>
                  </div>
                </label>
              </div>
              <div className="setup-bottom">
                <label className="charging-select">
                  <span className="field-label">Charge laptop through it?</span>
                  <select
                    name="charging"
                    value={
                      setup.laptop_charging === null
                        ? ""
                        : String(setup.laptop_charging)
                    }
                    onChange={(event) =>
                      updateSetup({
                        ...setup,
                        laptop_charging:
                          event.target.value === ""
                            ? null
                            : event.target.value === "true",
                      })
                    }
                  >
                    <option value="">Unknown</option>
                    <option value="true">Required</option>
                    <option value="false">Not needed</option>
                  </select>
                </label>
                <label className="refresh">
                  <span className="field-label">Refresh</span>
                  <select
                    name="refresh"
                    value={setup.refresh_rate_hz ?? ""}
                    onChange={(event) =>
                      updateSetup({
                        ...setup,
                        refresh_rate_hz: event.target.value
                          ? Number(event.target.value)
                          : null,
                      })
                    }
                  >
                    <option value="" disabled>
                      Choose refresh
                    </option>
                    {setup.refresh_rate_hz &&
                      ![30, 60].includes(setup.refresh_rate_hz) && (
                        <option value={setup.refresh_rate_hz}>
                          {setup.refresh_rate_hz} Hz
                        </option>
                      )}
                    <option value="60">60 Hz</option>
                    <option value="30">30 Hz</option>
                  </select>
                </label>
              </div>
            </div>
          </details>
          {catalogError && (
            <div className="catalog-error" role="alert">
              <div>
                <strong>We couldn’t load the device list.</strong>
                <span>
                  Make sure the PortPilot API is running and reachable, then
                  retry.
                </span>
              </div>
              <button
                className="catalog-retry"
                type="button"
                onClick={() => setCatalogAttempt((attempt) => attempt + 1)}
              >
                Try again
              </button>
            </div>
          )}
          {!catalogError && (
            <button
              className="submit"
              type="submit"
              disabled={
                loading ||
                catalogLoading ||
                parsing ||
                (parsedSetup !== null && !parsedSetupReviewed) ||
                !catalog ||
                !catalog.laptops.length ||
                !catalog.accessories.length ||
                !laptopId ||
                !accessoryId
              }
            >
              {loading ? (
                "Checking specifications…"
              ) : catalogLoading || !catalog ? (
                "Loading devices…"
              ) : !catalog.laptops.length || !catalog.accessories.length ? (
                "Catalogue unavailable"
              ) : (
                <>
                  Check my setup <span>→</span>
                </>
              )}
            </button>
          )}
          {error && (
            <p className="error-banner form-error" role="alert">
              {error}
            </p>
          )}
          <p className="privacy-note">
            <span>✳</span> Checks use documented specs. If something can’t be
            verified, we’ll say so.
          </p>
        </form>

        <div
          className="sr-only"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {announcement}
        </div>
        <aside className="result-panel" id="result-panel">
          {loading ? (
            <div className="checking-result">
              <span className="loading-spinner" aria-hidden="true" />
              <h2>Checking your setup</h2>
              <p>Comparing your devices with their published specifications…</p>
            </div>
          ) : !result ? (
            <div className="empty-result">
              <span className="result-kicker">YOUR RESULT</span>
              <h2>Your answer will appear here</h2>
              <p>
                Choose your devices, then check whether they support your setup.
              </p>
              <ol className="empty-steps">
                <li>Choose your laptop model</li>
                <li>Choose your dock, hub or charger</li>
                <li>Press “Check my setup”</li>
              </ol>
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
              <h2 className="verdict-title">{resultHeading}</h2>
              <p className="verdict-summary">{result.summary}</p>
              {result.verdict === "insufficient_data" && (
                <p className="result-caveat">
                  Not verified means we don’t have enough published information;
                  it doesn’t prove the setup won’t work.
                </p>
              )}
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
              <p className="share-explainer">
                This link restores your selections and reruns the check using
                the current catalogue and rules. It does not save this result as
                a snapshot.
              </p>
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
                        ? "NOT VERIFIED"
                        : item.status === "passed"
                          ? "SUPPORTED"
                          : "NOT SUPPORTED"}
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
              <div className="evidence-list">
                {groupEvidence(result.evidence).map(([url, records]) => (
                  <details className="evidence-source" key={url}>
                    <summary>
                      <span>{records[0].title}</span>
                      <small>{records.length} records</small>
                    </summary>
                    <div className="evidence-records">
                      {records.map((item) => (
                        <a
                          className="evidence-card"
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          key={item.id}
                        >
                          <span className="evidence-check">↗</span>
                          <small>“{item.excerpt}”</small>
                        </a>
                      ))}
                    </div>
                  </details>
                ))}
              </div>
              <details className="result-report">
                <summary>Think this result is wrong? Report it</summary>
                <p>
                  We’ll send the selected models, requested setup, verdict,
                  rules version, and your optional note. We don’t include serial
                  numbers, contact details, browsing data, or setup
                  descriptions. Please don’t include personal or secret
                  information in the note.
                </p>
                <form onSubmit={submitResultReport}>
                  <label htmlFor="report-note">
                    What seems wrong? (optional)
                  </label>
                  <textarea
                    id="report-note"
                    maxLength={1000}
                    value={reportNote}
                    onChange={(event) => setReportNote(event.target.value)}
                    rows={3}
                  />
                  <button type="submit" disabled={reporting}>
                    {reporting ? "Sending…" : "Send report"}
                  </button>
                  {reportMessage && <p role="status">{reportMessage}</p>}
                </form>
              </details>
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
