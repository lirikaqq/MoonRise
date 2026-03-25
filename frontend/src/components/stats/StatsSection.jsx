export default function StatsSection() {
  return (
    <section className="stats-section">
      <div className="stats-wrap">

        <div className="stats-top reveal">
          <div className="stats-bars">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span className="stats-title">STATS</span>
          <div className="stats-line"></div>
        </div>

        <div className="stats-card reveal reveal-delay-1">
          <div className="stats-grid">

            <div className="stats-item reveal reveal-delay-1">
              <div className="stats-value">6</div>
              <div className="stats-label">ТУРНИРОВ ПРОВЕДЕНО</div>
            </div>

            <div className="stats-item reveal reveal-delay-2">
              <div className="stats-value">100+</div>
              <div className="stats-label">УЧАСТНИКОВ</div>
            </div>

            <div className="stats-item reveal reveal-delay-3">
              <div className="stats-value">100+</div>
              <div className="stats-label">КОМАНД</div>
            </div>

            <div className="stats-item reveal reveal-delay-4">
              <div className="stats-value">18</div>
              <div className="stats-label">ПОБЕДИТЕЛЕЙ</div>
            </div>

          </div>
        </div>

      </div>
    </section>
  );
}