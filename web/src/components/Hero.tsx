interface HeroProps {
  onTryExample: () => void;
  sampleDisabled: boolean;
}

export function Hero({ onTryExample, sampleDisabled }: HeroProps) {
  return (
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
          onClick={onTryExample}
          disabled={sampleDisabled}
        >
          Try a sample report <span aria-hidden="true">→</span>
        </button>
      </div>
      <p className="sample-detail">
        IdeaPad Slim 3 14IRH10R + Anker Nano Hub A83D2 · one 1080p display and
        laptop charging.
      </p>
    </section>
  );
}
