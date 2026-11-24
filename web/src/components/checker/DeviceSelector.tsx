import Link from "next/link";
import type {
  Accessory,
  Catalog,
  CompatibleItem,
  Laptop,
} from "@/types/checker";
import { groupEvidence } from "@/utils/evidence";

interface DeviceSelectorProps {
  catalog: Catalog | null;
  catalogLoading: boolean;
  catalogError: boolean;
  laptopId: string;
  updateLaptopId: (id: string) => void;
  accessoryId: string;
  updateAccessoryId: (id: string) => void;
  laptopFilter: string;
  setLaptopFilter: (filter: string) => void;
  accessoryFilter: string;
  setAccessoryFilter: (filter: string) => void;
  selectedLaptop?: Laptop;
  selectedAccessory?: Accessory;
  filteredLaptops: Laptop[];
  filteredAccessories: Accessory[];
  loadingCompatible: boolean;
  showCompatibleBrowser: boolean;
  setShowCompatibleBrowser: (show: boolean) => void;
  compatibleList: CompatibleItem[] | null;
  fetchCompatibleAccessories: () => Promise<void>;
  selectCompatibleAccessory: (accId: string) => void;
}

export function DeviceSelector({
  catalog,
  catalogLoading,
  catalogError,
  laptopId,
  updateLaptopId,
  accessoryId,
  updateAccessoryId,
  laptopFilter,
  setLaptopFilter,
  accessoryFilter,
  setAccessoryFilter,
  selectedLaptop,
  selectedAccessory,
  filteredLaptops,
  filteredAccessories,
  loadingCompatible,
  showCompatibleBrowser,
  setShowCompatibleBrowser,
  compatibleList,
  fetchCompatibleAccessories,
  selectCompatibleAccessory,
}: DeviceSelectorProps) {
  return (
    <>
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
        <div
          style={{
            marginTop: "4px",
            display: "flex",
            justifyContent: "flex-end",
          }}
        >
          <button
            type="button"
            onClick={() =>
              setLaptopFilter(
                laptopFilter === "Standard Protocol" ? "" : "Standard Protocol",
              )
            }
            style={{
              background: "none",
              border: "none",
              padding: 0,
              color: "var(--accent, #3b82f6)",
              fontSize: "0.75rem",
              cursor: "pointer",
              textDecoration: "underline",
            }}
          >
            {laptopFilter === "Standard Protocol"
              ? "Show all laptops"
              : "Can't find your model? Use a protocol profile"}
          </button>
        </div>
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
            <a href={url} target="_blank" rel="noreferrer" key={records[0].id}>
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
            <strong>ChromeOS:</strong> Settings → About ChromeOS → Diagnostics,
            or check the label on the device.
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
                  Evaluated for requested setup ({compatibleList.length} items):
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
                                  : item.verdict === "compatible_with_limits"
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
        <div
          style={{
            marginTop: "4px",
            display: "flex",
            justifyContent: "flex-end",
          }}
        >
          <button
            type="button"
            onClick={() =>
              setAccessoryFilter(
                accessoryFilter === "Standard Protocol"
                  ? ""
                  : "Standard Protocol",
              )
            }
            style={{
              background: "none",
              border: "none",
              padding: 0,
              color: "var(--accent, #3b82f6)",
              fontSize: "0.75rem",
              cursor: "pointer",
              textDecoration: "underline",
            }}
          >
            {accessoryFilter === "Standard Protocol"
              ? "Show all accessories"
              : "Can't find your accessory? Use a protocol profile"}
          </button>
        </div>
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
          {groupEvidence(selectedAccessory.evidence).map(([url, records]) => (
            <a href={url} target="_blank" rel="noreferrer" key={records[0].id}>
              {records[0].title} ↗
            </a>
          ))}
        </details>
      )}
      <p className="catalog-help">
        Not sure which version you have? Check its product code on the label or
        manufacturer page; don’t choose a similar-looking model.
      </p>
    </>
  );
}
