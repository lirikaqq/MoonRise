export default function HeroSection() {
  return (
    <section className="hero-section">

      <div className="hero-layout">
        <div className="hero-content">

          <h1 className="hero-title">
            <span className="hero-title-light">RISE TO THE</span>
            <span className="hero-title-accent">MOON</span>
          </h1>

          <div className="hero-text-wrap">
            <div className="hero-text-bar"></div>
            <p>
              MOONRISE ОБЪЕДИНЯЕТ ТЕХ, КТО ГОТОВ{" "}
              <span className="accent">СИЯТЬ ЯРЧЕ.</span>
              <br />
              МЫ ПРОВОДИМ ТУРНИРЫ ВСЕХ ФОРМАТОВ — ОТ МИНИ-ИВЕНТОВ
              <br />
              ДО МАСШТАБНЫХ ТУРНИРОВ.
              <br />
              СТАНЬ ЧАСТЬЮ ПРОЕКТА, ПОБЕЖДАЙ И{" "}
              <span className="accent">ЗАНИМАЙ СВОЁ МЕСТО СРЕДИ ЗВЁЗД.</span>
            </p>
          </div>

          <div className="hero-button-row">
            <a href="#" className="cyber-button">
              JOIN DISCORD
            </a>
          </div>

        </div>
      </div>

      <div className="hero-visual">
        <div className="hero-ring"></div>
        <img
          className="hero-mascot"
          src="/assets/images/mascot.png"
          alt="MoonRise Mascot"
        />
      </div>

      <div className="hero-bottom-link">
        <a href="#tournament">
          <span className="hero-bottom-link-dot"></span>
          UPCOMING TOURNAMENT
        </a>
        <div className="hero-bottom-arrow"></div>
      </div>

    </section>
  );
}