import {
  AlertTriangle,
  Check,
  ChevronRight,
  Info,
  ShieldAlert,
} from "lucide-react";
import type { Alert, Route } from "@/lib/offshore-types";

type DecisionPanelProps = {
  routes: Route[];
  selectedRoute: Route;
  alerts: Alert[];
  onSelectRoute: (id: string) => void;
  onFocusAlert: (alert: Alert) => void;
};

export default function DecisionPanel({
  routes,
  selectedRoute,
  alerts,
  onSelectRoute,
  onFocusAlert,
}: DecisionPanelProps) {
  return (
    <aside className="route-options-panel" aria-label="Route Options and Comparison">
      {/* Header matching Image 2 */}
      <div className="options-panel-header">
        <span className="options-title">ROUTE OPTIONS</span>
        <span className="options-count">{routes.length} CANDIDATES</span>
      </div>

      {/* Candidate Route Cards matching Image 2 */}
      <div className="route-cards-stack">
        {routes.map((route) => {
          const isSelected = route.id === selectedRoute.id;
          const isRust = route.riskScore >= 0.45 || route.objective === "Fastest";
          const isSafest = route.objective === "Safest";
          const isFuel = route.objective === "Fuel Efficient";

          let barClass = "bar-neutral";
          if (isSelected) barClass = "bar-selected";
          else if (isSafest) barClass = "bar-safest";
          else if (isRust) barClass = "bar-rust";
          else if (isFuel) barClass = "bar-fuel";

          return (
            <button
              key={route.id}
              type="button"
              className={`route-item-card ${isSelected ? "is-selected" : ""} ${barClass}`}
              onClick={() => onSelectRoute(route.id)}
            >
              {/* Card Top */}
              <div className="card-top-row">
                <div className="card-name-group">
                  <strong className="card-route-title">{route.name}</strong>
                  {route.objective === "Recommended" ? (
                    <span className="badge-recommended">Recommended</span>
                  ) : (
                    <span className="card-route-sub">{route.objective}</span>
                  )}
                </div>
                {isSelected && <Check size={16} className="selected-check-icon" strokeWidth={2.5} />}
              </div>

              {/* 3 Metric Columns in IBM Plex Mono */}
              <div className="card-metrics-grid">
                <div className="metric-col">
                  <span className="metric-num">{route.distanceKm.toLocaleString()}</span>
                  <span className="metric-dim">km</span>
                </div>
                <div className="metric-col">
                  <span className="metric-num">{route.etaHours}</span>
                  <span className="metric-dim">h</span>
                </div>
                <div className="metric-col">
                  <span
                    className={`metric-num ${
                      isRust ? "num-rust" : isSelected ? "num-green" : "num-neutral"
                    }`}
                  >
                    {Math.round(route.riskScore * 100)}
                  </span>
                  <span className="metric-dim">/100</span>
                </div>
              </div>

              {/* Card Footer */}
              <div className="card-footer-row">
                <span className="exposure-text">{route.exposure}</span>
                <ChevronRight size={13} className="chevron-arrow" />
              </div>
            </button>
          );
        })}
      </div>

      {/* Expanded Rationale & Alerts section (available on scroll) */}
      <div className="options-secondary-section">
        {/* Selected Route Assessment */}
        <div className="selected-summary-box">
          <div className="summary-kicker">
            <span>SELECTED ROUTE RATIONALE</span>
            <span className="badge-calc">ESTIMATE</span>
          </div>
          <p className="summary-desc">
            <strong>{selectedRoute.name}</strong> keeps estimated iceberg encounters below allowable
            risk bounds with an optimal speed curve.
          </p>
        </div>

        {/* Hazard Alerts */}
        <div className="alerts-sub-block">
          <div className="alerts-kicker">
            <span className="alerts-kicker-title">
              <ShieldAlert size={12} /> ROUTE ALERTS
            </span>
            <span className="alerts-kicker-badge">
              {alerts.filter((a) => a.severity === "high").length} HIGH
            </span>
          </div>

          <div className="alerts-cards">
            {alerts.slice(0, 2).map((alert) => (
              <button
                key={alert.id}
                type="button"
                className={`alert-micro-card ${alert.severity === "high" ? "alert-high" : "alert-normal"}`}
                onClick={() => onFocusAlert(alert)}
              >
                <span className="alert-micro-icon">
                  {alert.severity === "high" ? (
                    <AlertTriangle size={13} className="icon-rust" />
                  ) : (
                    <Info size={13} className="icon-neutral" />
                  )}
                </span>
                <div className="alert-micro-text">
                  <strong className="alert-micro-title">{alert.title}</strong>
                  <span className="alert-micro-meta">{alert.time} · {alert.hazardType}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <div className="panel-disclaimer-note">
          <p>
            Antarctic navigation decision support. Metrics are simulated estimates, not autonomous instructions.
          </p>
        </div>
      </div>
    </aside>
  );
}
