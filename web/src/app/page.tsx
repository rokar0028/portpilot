"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { Hero } from "@/components/Hero";
import { Glossary } from "@/components/Glossary";
import { Footer } from "@/components/Footer";
import { DeviceSelector } from "@/components/checker/DeviceSelector";
import { SetupForm } from "@/components/checker/SetupForm";
import { ResultPanel } from "@/components/checker/ResultPanel";
import type {
  Catalog,
  CompatibleItem,
  CompatibleResponse,
  ParsedSetup,
  Result,
  Setup,
  SnapshotInfo,
} from "@/types/checker";
import {
  API,
  loadCatalog as fetchCatalog,
  loadCompatibleAccessories,
  loadSnapshot,
  parseSetupDescription,
  runCompatibilityCheck,
} from "@/lib/api";
import {
  buildResultUrl,
  defaultSetup,
  restoreSelectionState,
} from "@/lib/url-state";

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
  const [setup, setSetup] = useState<Setup>(defaultSetup);
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
  const [snapshotInfo, setSnapshotInfo] = useState<SnapshotInfo | null>(null);
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
      const data = await loadCompatibleAccessories(laptopId, setup);
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
      const parsed = await parseSetupDescription(setupDescription);
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
      const nextResult = await runCompatibilityCheck(
        nextLaptopId,
        nextAccessoryId,
        nextSetup,
      );
      if (requestVersion !== checkRequestVersion.current) return false;
      setResult(nextResult);
      window.history.replaceState(
        {},
        "",
        buildResultUrl(
          window.location.href,
          nextLaptopId,
          nextAccessoryId,
          nextSetup,
        ),
      );
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
        const data = await fetchCatalog();
        if (active) {
          const params = new URLSearchParams(window.location.search);
          const sharedSnapshot = params.get("snapshot");
          if (sharedSnapshot) {
            try {
              const snap = (await loadSnapshot(sharedSnapshot)) as {
                laptop_id: string;
                accessory_id: string;
                setup: Setup;
                verdict: string;
                summary: string;
                limits: string[];
                requirements: Result["requirements"];
                evidence: Result["evidence"];
                rule_engine_version: string;
                id: string;
                created_at: string;
              } | null;
              if (snap) {
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

          const restored = restoreSelectionState(
            params,
            data.laptops,
            data.accessories,
          );
          const nextLaptop = restored.laptopId;
          const nextAccessory = restored.accessoryId;
          const nextSetup = restored.setup;
          setCatalog(data);
          setLaptopId(nextLaptop);
          setAccessoryId(nextAccessory);
          setSetup(nextSetup);
          if (nextLaptop && nextAccessory) {
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
      <TopBar />
      <Hero
        onTryExample={() => void tryExample()}
        sampleDisabled={!catalog || loading}
      />

      <section className="workspace">
        <form className="check-form" onSubmit={submit}>
          <DeviceSelector
            catalog={catalog}
            catalogLoading={catalogLoading}
            catalogError={catalogError}
            laptopId={laptopId}
            updateLaptopId={updateLaptopId}
            accessoryId={accessoryId}
            updateAccessoryId={updateAccessoryId}
            laptopFilter={laptopFilter}
            setLaptopFilter={setLaptopFilter}
            accessoryFilter={accessoryFilter}
            setAccessoryFilter={setAccessoryFilter}
            selectedLaptop={selectedLaptop}
            selectedAccessory={selectedAccessory}
            filteredLaptops={filteredLaptops}
            filteredAccessories={filteredAccessories}
            loadingCompatible={loadingCompatible}
            showCompatibleBrowser={showCompatibleBrowser}
            setShowCompatibleBrowser={setShowCompatibleBrowser}
            compatibleList={compatibleList}
            fetchCompatibleAccessories={fetchCompatibleAccessories}
            selectCompatibleAccessory={selectCompatibleAccessory}
          />

          <SetupForm
            setup={setup}
            updateSetup={updateSetup}
            setupDescription={setupDescription}
            setSetupDescription={setSetupDescription}
            parsing={parsing}
            parseDescription={parseDescription}
            parsedSetup={parsedSetup}
            parsedSetupReviewed={parsedSetupReviewed}
            setParsedSetupReviewed={setParsedSetupReviewed}
            catalogError={catalogError}
            catalogLoading={catalogLoading}
            loading={loading}
            catalog={catalog}
            laptopId={laptopId}
            accessoryId={accessoryId}
            error={error}
            setCatalogAttempt={setCatalogAttempt}
          />
        </form>

        <div
          className="sr-only"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {announcement}
        </div>

        <ResultPanel
          loading={loading}
          result={result}
          resultHeading={resultHeading}
          selectedLaptop={selectedLaptop}
          selectedAccessory={selectedAccessory}
          laptopId={laptopId}
          accessoryId={accessoryId}
          setup={setup}
          snapshotInfo={snapshotInfo}
          setSnapshotInfo={setSnapshotInfo}
          runCheck={runCheck}
          copyShareLink={copyShareLink}
          shareMessage={shareMessage}
          submitResultReport={submitResultReport}
          reportNote={reportNote}
          setReportNote={setReportNote}
          reporting={reporting}
          reportMessage={reportMessage}
        />
      </section>

      <Glossary />
      <Footer />
    </main>
  );
}
