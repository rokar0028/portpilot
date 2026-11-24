export function Glossary() {
  return (
    <section className="glossary" aria-labelledby="glossary-title">
      <div>
        <span className="eyebrow">QUICK REFERENCE</span>
        <h2 id="glossary-title">A few useful terms</h2>
      </div>
      <details>
        <summary>USB-C</summary>
        <p>
          The connector shape. By itself, USB-C does not guarantee video output,
          charging, or a particular data speed.
        </p>
      </details>
      <details>
        <summary>DisplayPort Alt Mode</summary>
        <p>
          A way for a USB-C port to carry DisplayPort video to a display or hub.
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
  );
}
