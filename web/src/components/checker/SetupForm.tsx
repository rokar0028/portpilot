import type { Dispatch, SetStateAction } from "react";
import type { Catalog, ParsedSetup, Setup } from "@/types/checker";

interface SetupFormProps {
  setup: Setup;
  updateSetup: (nextSetup: Setup) => void;
  setupDescription: string;
  setSetupDescription: (desc: string) => void;
  parsing: boolean;
  parseDescription: () => Promise<void>;
  parsedSetup: ParsedSetup | null;
  parsedSetupReviewed: boolean;
  setParsedSetupReviewed: (reviewed: boolean) => void;
  catalogError: boolean;
  catalogLoading: boolean;
  loading: boolean;
  catalog: Catalog | null;
  laptopId: string;
  accessoryId: string;
  error: string;
  setCatalogAttempt: Dispatch<SetStateAction<number>>;
}

export function SetupForm({
  setup,
  updateSetup,
  setupDescription,
  setSetupDescription,
  parsing,
  parseDescription,
  parsedSetup,
  parsedSetupReviewed,
  setParsedSetupReviewed,
  catalogError,
  catalogLoading,
  loading,
  catalog,
  laptopId,
  accessoryId,
  error,
  setCatalogAttempt,
}: SetupFormProps) {
  return (
    <>
      <div className="divider" />
      <div className="section-head compact">
        <div>
          <span className="step">02</span>
          <h2>Screen &amp; charging</h2>
        </div>
      </div>
      <p className="setup-default-note">
        By default, we’ll check one 1080p screen at 60 Hz and laptop charging.
        Adjust these if your setup is different.
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
              Only this description is sent to the configured parsing provider.
              Don’t include personal information.
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
                    Not checked: {parsedSetup.unsupported_requests.join("; ")}
                  </p>
                )}
                {Object.entries(parsedSetup.setup).some(
                  ([, value]) => value === null,
                ) && (
                  <p>
                    Some fields are unknown. Fill in any requirement you want
                    checked.
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
              Make sure the PortPilot API is running and reachable, then retry.
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
    </>
  );
}
