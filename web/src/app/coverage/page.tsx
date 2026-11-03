"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Catalog = {
  laptops: {
    id: string;
    brand: string;
    name: string;
    model_code: string | null;
  }[];
  accessories: {
    id: string;
    brand: string;
    name: string;
    model_code: string | null;
    category: string;
  }[];
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export default function CoveragePage() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    fetch(`${API}/devices`)
      .then((response) => {
        if (!response.ok) throw new Error("Catalogue unavailable");
        return response.json() as Promise<Catalog>;
      })
      .then((data) => {
        if (active) setCatalog(data);
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const categories = catalog
    ? [...new Set(catalog.accessories.map((item) => item.category))]
    : [];

  return (
    <main className="shell coverage-shell">
      <header className="topbar">
        <Link className="brand" href="/">
          <span className="brand-mark">P</span> portpilot
        </Link>
        <Link className="coverage-nav" href="/">
          Back to checker
        </Link>
      </header>
      <section className="coverage-hero">
        <span className="eyebrow">CATALOGUE SCOPE</span>
        <h1>Know what we cover.</h1>
        <p>
          PortPilot checks documented laptop and accessory capabilities. The
          catalogue is deliberately curated, so an unknown result can mean the
          manufacturer information needed for your setup is not available yet.
        </p>
      </section>

      <section
        className="coverage-stats"
        aria-label="Verified catalogue totals"
      >
        <article>
          <strong>
            {catalog ? catalog.laptops.length : error ? "—" : "…"}
          </strong>
          <span>verified laptops</span>
        </article>
        <article>
          <strong>
            {catalog ? catalog.accessories.length : error ? "—" : "…"}
          </strong>
          <span>verified accessories</span>
        </article>
        <article>
          <strong>{catalog ? categories.length : "—"}</strong>
          <span>accessory categories</span>
        </article>
      </section>
      {error && (
        <p className="coverage-error" role="status">
          Live catalogue counts are unavailable right now. Please try again
          later.
        </p>
      )}
      {catalog && (!catalog.laptops.length || !catalog.accessories.length) && (
        <p className="coverage-error" role="status">
          The verified catalogue is still being assembled. Some checks may not
          be available yet.
        </p>
      )}

      <section className="coverage-grid">
        <article>
          <span className="step">01</span>
          <h2>How evidence is handled</h2>
          <p>
            Published devices are reviewed against manufacturer documentation.
            Populated capabilities link to a source and a factual excerpt.
            Missing specifications stay unknown; PortPilot does not fill gaps
            from product-family assumptions or community reports.
          </p>
        </article>
        <article>
          <span className="step">02</span>
          <h2>What a result means</h2>
          <p>
            Compatible means the modeled requirements are documented as met.
            Works with limits identifies a documented constraint. Incompatible
            means a requirement is documented as unsupported. Insufficient data
            means the available sources cannot establish a safe answer.
          </p>
        </article>
        <article>
          <span className="step">03</span>
          <h2>Current boundaries</h2>
          <p>
            Coverage is limited to verified records and the setup fields offered
            by the checker. PortPilot does not search retailers, compare prices,
            diagnose hardware faults, or guarantee behavior beyond published
            specifications. Catalogue totals show verified records only.
          </p>
        </article>
      </section>
      {categories.length > 0 && (
        <p className="coverage-categories">
          Current accessory categories:{" "}
          {categories.join(", ").replaceAll("_", " ")}.
        </p>
      )}
      {catalog && (
        <section className="supported-devices" id="supported-devices">
          <div>
            <span className="eyebrow">CHECK YOUR MODEL</span>
            <h2>Currently supported devices</h2>
            <p>
              Match the full model name or product code before running a check.
              Similar model names can have different ports and capabilities.
            </p>
          </div>
          <div className="supported-device-columns">
            <article>
              <h3>Laptops</h3>
              <ul>
                {catalog.laptops.map((laptop) => (
                  <li key={laptop.id}>
                    <strong>{laptop.name}</strong>
                    <span>{laptop.model_code ?? laptop.brand}</span>
                  </li>
                ))}
              </ul>
            </article>
            <article>
              <h3>Accessories</h3>
              <ul>
                {catalog.accessories.map((accessory) => (
                  <li key={accessory.id}>
                    <strong>{accessory.name}</strong>
                    <span>
                      {accessory.model_code ?? accessory.brand} ·{" "}
                      {accessory.category.replaceAll("_", " ")}
                    </span>
                  </li>
                ))}
              </ul>
            </article>
          </div>
          <p className="unsupported-device-note">
            <strong>Can’t find an exact match?</strong> Don’t select a similar
            model. Check the product code on your laptop’s label or the
            manufacturer support page. PortPilot can only give a reliable result
            for models in this verified list.
          </p>
        </section>
      )}
      <footer>
        <span>PORTPILOT · EVIDENCE FIRST</span>
        <Link href="/">Run a compatibility check</Link>
      </footer>
    </main>
  );
}
