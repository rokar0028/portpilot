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
  displaylink_supported?: boolean | null;
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
type CompatibleItem = {
  accessory: Accessory;
  verdict: string;
  summary: string;
  limits: string[];
};
type CompatibleResponse = {
  laptop_id: string;
  laptop_name: string;
  total_evaluated: number;
  counts: Record<string, number>;
  results: CompatibleItem[];
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
  const [snapshotInfo, setSnapshotInfo] = useState<{
    id: string;
    createdAt: string;
    rulesVersion: string;
  } | null>(null);
  const [laptopFilter, setLaptopFilter] = useState("");
  const [accessoryFilter, setAccessoryFilter] = useState("");
  const [compatibleList, setCompatibleList] = useState<CompatibleItem[] | null>(
    null,
  );
  const [loadingCompatible, setLoadingCompatible] = useState(false);
  const [showCompatibleBrowser, setShowCompatibleBrowser] = useState(false);

  const normalizeSearch = (value: string) =>
    value.toLowerCase().replace(/[\s\-_]+/g, "");

  const filteredLaptops =
    catalog?.laptops.filter((lap) => {
      if (!laptopFilter.trim()) return true;
      const raw = laptopFilter.toLowerCase();
      const norm = normalizeSearch(laptopFilter);
      const nameNorm = normalizeSearch(lap.name);
      const codeNorm = lap.model_code ? normalizeSearch(lap.model_code) : "";
      return (
        lap.name.toLowerCase().includes(raw) ||
        nameNorm.includes(norm) ||
        (lap.model_code && lap.model_code.toLowerCase().includes(raw)) ||
        (codeNorm && codeNorm.includes(norm))
      );
    }) ?? [];

  const filteredAccessories =
    catalog?.accessories.filter((acc) => {
      if (!accessoryFilter.trim()) return true;
      const raw = accessoryFilter.toLowerCase();
      const norm = normalizeSearch(accessoryFilter);
      const nameNorm = normalizeSearch(acc.name);
      const codeNorm = acc.model_code ? normalizeSearch(acc.model_code) : "";
      return (
        acc.name.toLowerCase().includes(raw) ||
        nameNorm.includes(norm) ||
        (acc.model_code && acc.model_code.toLowerCase().includes(raw)) ||
        (codeNorm && codeNorm.includes(norm)) ||
        acc.category.toLowerCase().includes(raw)
      );
    }) ?? [];

  function updateLaptopId(value: string) {
    checkRequestVersion.current += 1;
    setLoading(false);
    setLaptopId(value);
    setResult(null);
    setSnapshotInfo(null);
    setCompatibleList(null);
    setShowCompatibleBrowser(false);
    setError("");
  }

  function updateAccessoryId(value: string) {
    checkRequestVersion.current += 1;
    setLoading(false);
    setAccessoryId(value);
    setResult(null);
    setSnapshotInfo(null);
    setError("");
    const accessory = catalog?.accessories.find((item) => item.id === value);
    if (accessory?.category === "usb_c_charger") {
      if (setup.external_displays === 1) {
        setSetup((prev) => ({ ...prev, external_displays: 0 }));
      }
    } else if (accessory && setup.external_displays === 0) {
      setSetup((prev) => ({ ...prev, external_displays: 1 }));
    }
  }

  function updateSetup(nextSetup: Setup) {
    checkRequestVersion.current += 1;
    setLoading(false);
    setSetup(nextSetup);
    if (parsedSetup) setParsedSetupReviewed(false);
    setResult(null);
    setSnapshotInfo(null);
    setError("");
  }

  async function fetchCompatibleAccessories() {
    if (!laptopId) return;
    setLoadingCompatible(true);
    setShowCompatibleBrowser(true);
    try {
      const qs = new URLSearchParams({
        displays: String(setup.external_displays ?? 1),
        resolution: setup.resolution ?? "1920x1080",
        refresh_rate_hz: String(setup.refresh_rate_hz ?? 60),
        laptop_charging: String(setup.laptop_charging ?? true),
      });
      const res = await fetch(
        `${API}/devices/laptops/${laptopId}/compatible-accessories?${qs}`,
      );
      if (!res.ok) throw new Error("Could not load compatible accessories");
      const data: CompatibleResponse = await res.json();
      setCompatibleList(data.results);
    } catch {
      setCompatibleList([]);
    } finally {
      setLoadingCompatible(false);
    }
  }

  function selectCompatibleAccessory(accId: string) {
    updateAccessoryId(accId);
    void runCheck(laptopId, accId, setup);
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
          const sharedSnapshot = params.get("snapshot");
          if (sharedSnapshot) {
            try {
              const snapResp = await fetch(
                `${API}/result-snapshots/${sharedSnapshot}`,
              );
              if (snapResp.ok) {
                const snap = await snapResp.json();
                setCatalog(data);
                setLaptopId(snap.laptop_id);
                setAccessoryId(snap.accessory_id);
                setSetup(snap.setup);
                setResult({
                  verdict: snap.verdict,
                  summary: snap.summary,
                  limits: snap.limits,
                  requirements: snap.requirements,
                  evidence: snap.evidence,
                  rule_engine_version: snap.rule_engine_version,
                });
                setSnapshotInfo({
                  id: snap.id,
                  createdAt: snap.created_at,
                  rulesVersion: snap.rule_engine_version,
                });
                return;
              }
            } catch {
              // fallback to regular URL params
            }
          }

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
          const hasDisplays = params.has("displays");
          const hasRefresh = params.has("refresh");
          const hasResolution = params.has("resolution");
          const hasCharging = params.has("charging");

          const rawDisplays = params.get("displays");
          const rawRefresh = params.get("refresh");
          const rawResolution = params.get("resolution");
          const rawCharging = params.get("charging");

          const parsedDisplays =
            rawDisplays !== null &&
            rawDisplays !== "" &&
            rawDisplays !== "null" &&
            !isNaN(Number(rawDisplays))
              ? Number(rawDisplays)
              : null;
          const parsedRefresh =
            rawRefresh !== null &&
            rawRefresh !== "" &&
            rawRefresh !== "null" &&
            !isNaN(Number(rawRefresh))
              ? Number(rawRefresh)
              : null;

          const nextDisplays = hasDisplays
            ? rawDisplays === "null" || rawDisplays === ""
              ? null
              : parsedDisplays !== null &&
                  parsedDisplays >= 0 &&
                  parsedDisplays <= 8
                ? parsedDisplays
                : 1
            : 1;

          const nextResolution = hasResolution
            ? rawResolution === "null" || rawResolution === ""
              ? null
              : rawResolution && rawResolution.length <= 30
                ? rawResolution
                : "1920x1080"
            : "1920x1080";

          const nextRefresh = hasRefresh
            ? rawRefresh === "null" || rawRefresh === ""
              ? null
              : parsedRefresh !== null &&
                  parsedRefresh >= 24 &&
                  parsedRefresh <= 240
                ? parsedRefresh
                : 60
            : 60;

          const nextCharging = hasCharging
            ? rawCharging === "true"
              ? true
              : rawCharging === "false"
                ? false
                : null
            : true;

          const nextSetup: Setup = {
            external_displays: nextDisplays,
            resolution: nextResolution,
            refresh_rate_hz: nextRefresh,
            laptop_charging: nextCharging,
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
      if (result && laptopId && accessoryId) {
        try {
          const resp = await fetch(`${API}/result-snapshots`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              laptop_id: laptopId,
              accessory_id: accessoryId,
              setup,
              verdict: result.verdict,
              summary: result.summary,
              limits: result.limits,
              requirements: result.requirements,
              evidence: result.evidence,
              rule_engine_version: result.rule_engine_version,
            }),
          });
          if (resp.ok) {
            const snap = await resp.json();
            const snapUrl = new URL(window.location.href);
            snapUrl.search = new URLSearchParams({
              snapshot: snap.id,
            }).toString();
            window.history.replaceState({}, "", snapUrl);
            await navigator.clipboard.writeText(snapUrl.toString());
            setSnapshotInfo({
              id: snap.id,
              createdAt: snap.created_at,
              rulesVersion: snap.rule_engine_version,
            });
            setShareMessage("Link copied");
            window.setTimeout(() => setShareMessage(""), 2600);
            return;
          }
        } catch {
          // fallback
        }
      }
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
          <div className="filter-input-wrap" style={{ marginBottom: "6px" }}>
            <input
              type="search"
              placeholder="Filter laptops (e.g. Slim 3, M2, ThinkPad)..."
              value={laptopFilter}
              onChange={(event) => setLaptopFilter(event.target.value)}
              aria-label="Filter laptops by name or model code"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "6px",
                border: "1px solid var(--border-color, #333)",
                background: "var(--input-bg, transparent)",
                color: "inherit",
                fontSize: "0.85rem",
              }}
            />
          </div>
          <div className="select-wrap">
            <select
              id="laptop"
              name="laptop_id"
              value={laptopId}
              onChange={(event) => updateLaptopId(event.target.value)}
              disabled={!catalog}
            >
              <option value="">Choose your exact laptop model</option>
              {filteredLaptops.map((laptop) => (
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

          {selectedLaptop && (
            <div
              className="compatible-accessories-section"
              style={{ marginTop: "12px", marginBottom: "8px" }}
            >
              <button
                type="button"
                className="compatible-lookup-btn"
                onClick={() => void fetchCompatibleAccessories()}
                disabled={loadingCompatible}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "7px 12px",
                  fontSize: "0.82rem",
                  fontWeight: 500,
                  borderRadius: "6px",
                  border: "1px solid var(--accent, #3b82f6)",
                  background: "rgba(59, 130, 246, 0.08)",
                  color: "inherit",
                  cursor: "pointer",
                }}
              >
                <span>⚡</span>
                {loadingCompatible
                  ? "Evaluating catalogue..."
                  : showCompatibleBrowser
                    ? "Refresh accessories for this laptop"
                    : `Browse compatible accessories for this ${selectedLaptop.name.split(" ")[0]}`}
              </button>

              {showCompatibleBrowser && compatibleList && (
                <div
                  className="compatible-browser-card"
                  style={{
                    marginTop: "10px",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-color, #333)",
                    background: "var(--card-bg, rgba(255, 255, 255, 0.03))",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "8px",
                    }}
                  >
                    <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>
                      Evaluated for requested setup ({compatibleList.length}{" "}
                      items):
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowCompatibleBrowser(false)}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "inherit",
                        cursor: "pointer",
                        fontSize: "0.8rem",
                      }}
                      aria-label="Close accessories browser"
                    >
                      ✕
                    </button>
                  </div>
                  {compatibleList.length === 0 ? (
                    <p
                      style={{
                        fontSize: "0.8rem",
                        color: "var(--muted, #888)",
                      }}
                    >
                      No accessories match this setup in the verified catalogue.
                    </p>
                  ) : (
                    <ul
                      style={{
                        listStyle: "none",
                        padding: 0,
                        margin: 0,
                        display: "flex",
                        flexDirection: "column",
                        gap: "6px",
                      }}
                    >
                      {compatibleList.map((item) => (
                        <li
                          key={item.accessory.id}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            padding: "6px 8px",
                            borderRadius: "4px",
                            background:
                              accessoryId === item.accessory.id
                                ? "rgba(59, 130, 246, 0.15)"
                                : "transparent",
                            border: "1px solid var(--border-color, #222)",
                            fontSize: "0.8rem",
                          }}
                        >
                          <div
                            style={{
                              flex: 1,
                              minWidth: 0,
                              marginRight: "8px",
                            }}
                          >
                            <div
                              style={{
                                fontWeight: 500,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                              }}
                            >
                              {item.accessory.name}
                            </div>
                            <div
                              style={{
                                fontSize: "0.72rem",
                                color: "var(--muted, #888)",
                              }}
                            >
                              {item.accessory.model_code
                                ? `${item.accessory.model_code} · `
                                : ""}
                              <span
                                style={{
                                  color:
                                    item.verdict === "compatible"
                                      ? "#22c55e"
                                      : item.verdict ===
                                          "compatible_with_limits"
                                        ? "#eab308"
                                        : "#ef4444",
                                }}
                              >
                                {item.verdict === "compatible"
                                  ? "✓ Compatible"
                                  : item.verdict === "compatible_with_limits"
                                    ? "! Works with limits"
                                    : item.verdict === "incompatible"
                                      ? "✕ Incompatible"
                                      : "? Insufficient data"}
                              </span>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() =>
                              selectCompatibleAccessory(item.accessory.id)
                            }
                            style={{
                              padding: "4px 8px",
                              fontSize: "0.75rem",
                              borderRadius: "4px",
                              border: "1px solid var(--border-color, #444)",
                              background: "var(--input-bg, transparent)",
                              color: "inherit",
                              cursor: "pointer",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {accessoryId === item.accessory.id
                              ? "Selected"
                              : "Select"}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="connector">
            <span />
            <span />
            <span />
          </div>

          <label className="field-label" htmlFor="accessory">
            Connect a dock, hub or charger
          </label>
          <div className="filter-input-wrap" style={{ marginBottom: "6px" }}>
            <input
              type="search"
              placeholder="Filter accessories (e.g. Anker, Dock, Hub)..."
              value={accessoryFilter}
              onChange={(event) => setAccessoryFilter(event.target.value)}
              aria-label="Filter accessories by name or model code"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "6px",
                border: "1px solid var(--border-color, #333)",
                background: "var(--input-bg, transparent)",
                color: "inherit",
                fontSize: "0.85rem",
              }}
            />
          </div>
          <div className="select-wrap">
            <select
              id="accessory"
              name="accessory_id"
              value={accessoryId}
              onChange={(event) => updateAccessoryId(event.target.value)}
              disabled={!catalog}
            >
              <option value="">Choose the exact model</option>
              {filteredAccessories.map((accessory) => (
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
                  : ["portable_monitor", "external_display"].includes(
                        selectedAccessory.category,
                      )
                    ? `Display input: up to ${selectedAccessory.hdmi_max_resolution ?? "not documented"}${selectedAccessory.hdmi_max_refresh_hz ? ` at ${selectedAccessory.hdmi_max_refresh_hz} Hz` : ""}`
                    : `Display outputs: ${selectedAccessory.hdmi_port_count ?? "not documented"} HDMI · up to ${selectedAccessory.hdmi_max_resolution ?? "not documented"}${selectedAccessory.hdmi_max_refresh_hz ? ` at ${selectedAccessory.hdmi_max_refresh_hz} Hz` : ""}`}
                {selectedAccessory.category !== "usb_c_charger" && (
                  <>
                    <br />
                    Laptop must support USB-C video:{" "}
                    {selectedAccessory.displaylink_supported
                      ? "no (DisplayLink USB graphics)"
                      : selectedAccessory.requires_usb_c_dp_alt_mode === true
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
                      {setup.external_displays !== null &&
                        ![0, 1, 2, 3, 4].includes(setup.external_displays) && (
                          <option value={setup.external_displays}>
                            {setup.external_displays} displays
                          </option>
                        )}
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
              {snapshotInfo && (
                <div
                  className="snapshot-notice"
                  style={{
                    padding: "8px 12px",
                    background: "rgba(59, 130, 246, 0.12)",
                    border: "1px solid rgba(59, 130, 246, 0.3)",
                    borderRadius: "6px",
                    margin: "12px 0",
                    fontSize: "0.85rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span>
                    📌 Pinned snapshot from{" "}
                    {new Date(snapshotInfo.createdAt).toLocaleDateString()}
                  </span>
                  <button
                    type="button"
                    style={{
                      textDecoration: "underline",
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: "inherit",
                      fontWeight: 500,
                    }}
                    onClick={() => {
                      setSnapshotInfo(null);
                      void runCheck(laptopId, accessoryId, setup);
                    }}
                  >
                    Rerun with latest catalogue ↻
                  </button>
                </div>
              )}
              <div
                className={`verdict-icon ${result.verdict}`}
                aria-hidden="true"
              >
                {result.verdict === "compatible"
                  ? "✓"
                  : result.verdict === "compatible_with_limits"
                    ? "!"
                    : result.verdict === "incompatible"
                      ? "×"
                      : "?"}
              </div>
              <h2 className="verdict-title">{resultHeading}</h2>
              <p className="verdict-summary">{result.summary}</p>
              {result.verdict === "insufficient_data" && (
                <div
                  className="insufficient-data-box"
                  role="region"
                  aria-label="Missing specifications breakdown"
                >
                  <div className="insufficient-data-header">
                    <span className="insufficient-icon" aria-hidden="true">
                      ℹ
                    </span>
                    <strong>What manufacturer data is missing?</strong>
                  </div>
                  <p className="result-caveat">
                    Not verified means the manufacturer documentation is
                    incomplete or unavailable; it doesn’t prove the setup won’t
                    work. PortPilot refuses to guess undocumented
                    specifications.
                  </p>
                  <ul
                    className="missing-specs-list"
                    aria-label="Unverified requirements"
                  >
                    {result.requirements
                      .filter((req) => req.status === "unknown")
                      .map((req) => (
                        <li key={req.name}>
                          <strong>{req.name}:</strong> {req.detail}
                          <div
                            style={{
                              marginTop: "4px",
                              fontSize: "0.8rem",
                              color: "var(--muted, #94a3b8)",
                              lineHeight: 1.4,
                            }}
                          >
                            {req.name.includes("Physical connection") &&
                              "Guidance: Check the laptop’s tech specs page for the exact number and type of USB-C ports."}
                            {req.name.includes("video") &&
                              "Guidance: Check whether the manufacturer explicitly lists DisplayPort Alt Mode or video output."}
                            {req.name.includes("Display count") &&
                              "Guidance: Check CPU/GPU specs for the maximum number of external displays supported."}
                            {req.name.includes("mode") &&
                              "Guidance: Look for the maximum external resolution and refresh rate in the user manual."}
                            {req.name.includes("Charging") &&
                              "Guidance: Check the original power adapter wattage and USB Power Delivery input requirements."}
                          </div>
                        </li>
                      ))}
                  </ul>
                  <div style={{ marginTop: "10px", fontSize: "0.82rem" }}>
                    <Link
                      href="/coverage#unknown-specifications"
                      style={{
                        color: "#1d4ed8",
                        textDecoration: "underline",
                      }}
                    >
                      How PortPilot handles unknown specifications &amp;
                      evidence standards →
                    </Link>
                  </div>
                </div>
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
                <div
                  className="limit-callout"
                  role="region"
                  aria-label="Hardware limitations and constraints"
                >
                  <div className="limit-callout-header">
                    <span aria-hidden="true">⚠</span>
                    <strong>Hardware constraints &amp; limitations</strong>
                  </div>
                  <ul className="limit-list" aria-label="Known limitations">
                    {result.limits.map((limit) => (
                      <li key={limit}>{limit}</li>
                    ))}
                  </ul>
                </div>
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
        <Link href="/coverage">Coverage &amp; limitations</Link>
      </footer>
    </main>
  );
}
