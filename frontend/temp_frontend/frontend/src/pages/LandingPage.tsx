import { useLocation } from "wouter";
import { Anchor, ArrowRight, Globe, Route as RouteIcon, Shield, Waves } from "lucide-react";

export default function LandingPage() {
  const [, setLocation] = useLocation();

  return (
    <div className="landing-page">
      {/* Header */}
      <header className="landing-header">
        <div className="brand">
          <div className="brand-mark"><span /><span /><span /></div>
          <div><strong>OFFSHORE</strong><small>navigation intelligence</small></div>
        </div>
      </header>

      {/* Hero */}
      <section className="landing-hero">
        <span className="landing-eyebrow">DECISION SUPPORT PLATFORM</span>
        <h1>Intelligent Maritime<br />Navigation & Decision Support</h1>
        <p>A geospatial decision-support platform for safer, smarter and more informed maritime operations.</p>
        <button className="landing-cta" onClick={() => setLocation("/dashboard")}>
          Launch Dashboard <ArrowRight size={16} />
        </button>
      </section>

      {/* Capabilities */}
      <section className="landing-capabilities">
        <span className="landing-eyebrow">CORE CAPABILITIES</span>
        <div className="landing-cards">
          <div className="landing-card">
            <div className="landing-card-icon"><RouteIcon size={20} /></div>
            <h3>Route Intelligence</h3>
            <p>Risk-aware passage planning with multi-objective route comparison and recommendation.</p>
          </div>
          <div className="landing-card">
            <div className="landing-card-icon"><Shield size={20} /></div>
            <h3>Geospatial Risk Analysis</h3>
            <p>Dynamic risk surface modelling informed by sea-ice, iceberg and environmental forecast data.</p>
          </div>
          <div className="landing-card">
            <div className="landing-card-icon"><Anchor size={20} /></div>
            <h3>Vessel Intelligence</h3>
            <p>Vessel-specific parameters integrated into route scoring including ice-class and fuel profile.</p>
          </div>
          <div className="landing-card">
            <div className="landing-card-icon"><Waves size={20} /></div>
            <h3>Environmental Awareness</h3>
            <p>Forecast integration for sea-ice concentration, wave height and iceberg trajectory prediction.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <Globe size={14} />
        <span>Decision support for complex maritime environments.</span>
      </footer>
    </div>
  );
}
