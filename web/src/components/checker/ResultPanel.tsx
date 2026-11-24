import { FormEvent } from "react";
import Link from "next/link";
import type {
  Accessory,
  Laptop,
  Result,
  Setup,
  SnapshotInfo,
} from "@/types/checker";
import { groupEvidence, sourceCount } from "@/utils/evidence";

interface ResultPanelProps {
  loading: boolean;
  result: Result | null;
  resultHeading: string;
  selectedLaptop?: Laptop;
  selectedAccessory?: Accessory;
  laptopId: string;
  accessoryId: string;
  setup: Setup;
  snapshotInfo: SnapshotInfo | null;
  setSnapshotInfo: (info: SnapshotInfo | null) => void;
  runCheck: (
    laptopId: string,
    accessoryId: string,
    setup: Setup,
  ) => Promise<boolean>;
  copyShareLink: () => Promise<void>;
  shareMessage: string;
  submitResultReport: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  reportNote: string;
  setReportNote: (note: string) => void;
  reporting: boolean;
  reportMessage: string;
}

export function ResultPanel({
  loading,
  result,
  resultHeading,
  selectedLaptop,
  selectedAccessory,
  laptopId,
  accessoryId,
  setup,
  snapshotInfo,
  setSnapshotInfo,
  runCheck,
  copyShareLink,
  shareMessage,
  submitResultReport,
  reportNote,
  setReportNote,
  reporting,
  reportMessage,
}: ResultPanelProps) {
  return (
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
            <span className="version">RULES {result.rule_engine_version}</span>
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
          <div style={{ marginTop: "10px", marginBottom: "4px" }}>
            {result.evaluation_tier === "theoretical" ? (
              <span
                className="tier-badge theoretical"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "4px 9px",
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  letterSpacing: "0.04em",
                  borderRadius: "4px",
                  background: "rgba(147, 51, 234, 0.12)",
                  color: "#6b21a8",
                  border: "1px solid rgba(147, 51, 234, 0.25)",
                }}
              >
                <span aria-hidden="true">⚙</span> THEORETICAL PROTOCOL
                EVALUATION
              </span>
            ) : (
              <span
                className="tier-badge verified"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "4px 9px",
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  letterSpacing: "0.04em",
                  borderRadius: "4px",
                  background: "rgba(22, 101, 52, 0.1)",
                  color: "#166534",
                  border: "1px solid rgba(22, 101, 52, 0.25)",
                }}
              >
                <span aria-hidden="true">🛡</span> VERIFIED MANUFACTURER EVIDENCE
              </span>
            )}
          </div>
          {result.evaluation_tier === "theoretical" && (
            <div
              className="theoretical-notice"
              style={{
                marginTop: "6px",
                marginBottom: "8px",
                padding: "8px 12px",
                background: "rgba(168, 85, 247, 0.08)",
                border: "1px solid rgba(168, 85, 247, 0.2)",
                borderRadius: "6px",
                fontSize: "0.8rem",
                color: "var(--muted, #cbd5e1)",
                lineHeight: 1.4,
              }}
            >
              Evaluated against industry standard specifications (USB-IF / VESA
              / Thunderbolt). Confirms protocol and bandwidth feasibility; OEM
              firmware may impose custom limits.
            </div>
          )}
          <div className={`verdict-icon ${result.verdict}`} aria-hidden="true">
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
                Not verified means the manufacturer documentation is incomplete
                or unavailable; it doesn’t prove the setup won’t work. PortPilot
                refuses to guess undocumented specifications.
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
                  How PortPilot handles unknown specifications &amp; evidence
                  standards →
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
            This link restores your selections and reruns the check using the
            current catalogue and rules. It does not save this result as a
            snapshot.
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
              {sourceCount(result.evidence)} sources · {result.evidence.length}{" "}
              capability records
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
              We’ll send the selected models, requested setup, verdict, rules
              version, and your optional note. We don’t include serial numbers,
              contact details, browsing data, or setup descriptions. Please
              don’t include personal or secret information in the note.
            </p>
            <form onSubmit={submitResultReport}>
              <label htmlFor="report-note">What seems wrong? (optional)</label>
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
  );
}
