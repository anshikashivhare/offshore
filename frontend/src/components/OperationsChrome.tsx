import { useRef } from "react";
import {
  Activity,
  Calendar,
  CalendarDays,
  Clock,
  Clock3,
  CloudSnow,
  Database,
  Menu,
  Play,
  Satellite,
  Shield,
  ShieldAlert,
  Waves,
} from "lucide-react";
import type { ForecastMeta } from "@/lib/offshore-types";

export function AppHeader({
  onMenu,
  routeLabel,
  forecastDateTime,
}: {
  onMenu: () => void;
  routeLabel?: string;
  /** Computed forecast date+time string (e.g. "14 Sep 2026 · 16:00 UTC").
   *  When provided, replaces the static timestamp in the header pill. */
  forecastDateTime?: string;
}) {
  return (
    <header className="app-header" aria-label="Operational Header">
      <button
        className="mobile-menu-btn"
        onClick={onMenu}
        aria-label="Toggle mission planner menu"
      >
        <Menu size={18} />
      </button>

      {/* Brand: Mountain Emblem + OFFSHORE + NAVIGATION INTELLIGENCE */}
      <div className="header-brand-group">
        <div className="brand-logo-emblem">
          <svg width="34" height="28" viewBox="0 0 34 28" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 24L12 6L20 20L25 11L32 24H2Z" fill="#527C78" stroke="#183B43" strokeWidth="1.5" strokeLinejoin="round" />
            <path d="M12 6L16 13H8L12 6Z" fill="#F3F1EA" />
            <path d="M25 11L28 17H22L25 11Z" fill="#DCE5E5" />
          </svg>
        </div>
        <div className="brand-text-block">
          <span className="brand-name">OFFSHORE</span>
          <span className="brand-tagline">NAVIGATION INTELLIGENCE</span>
        </div>
      </div>

      {/* Center Pills matching Image 2 */}
      <div className="header-center-pills">
        {/* Pill 1: Antarctic sector */}
        <div className="header-pill">
          <span className="pill-dot-dark" />
          <span className="pill-label">Antarctic sector</span>
          <strong className="pill-val">{routeLabel || "Rothera → Casey"}</strong>
        </div>

        {/* Pill 2: Selected forecast date — updates with selectedDate + forecastHours */}
        <div className="header-pill">
          <CalendarDays size={13} className="pill-icon" />
          <span className="pill-mono-text">
            {forecastDateTime ?? "Live System Time"}
          </span>
        </div>
      </div>

      {/* Right Pills matching Image 2 */}
      <div className="header-right-group">
        {/* System status pill */}
        <div className="header-status-pill">
          <span className="status-dot-green" />
          <div className="status-pill-texts">
            <span className="status-line-1">System nominal</span>
            <span className="status-line-2">Last sync 04 min ago</span>
          </div>
        </div>

        {/* Dark Avatar Square matching Image 2 */}
        <div className="operator-square" title="Operator Console (Active)">
          <span>OC</span>
        </div>
      </div>
    </header>
  );
}

export function KpiStrip({ forecast, route, liveEnv }: { forecast: ForecastMeta, route?: any, liveEnv?: any }) {
  let avgIce = 0;
  let avgWave = 0;
  let riskScore = route ? route.riskScore : 0;
  
  if (liveEnv && liveEnv.waypoints && liveEnv.waypoints.length > 0) {
    const validIce = liveEnv.waypoints.filter((w: any) => w.env_conditions?.sea_ice_concentration !== undefined);
    const validWaves = liveEnv.waypoints.filter((w: any) => w.env_conditions?.wave_height !== undefined);
    if (validIce.length > 0) {
      avgIce = validIce.reduce((sum: number, w: any) => sum + w.env_conditions.sea_ice_concentration, 0) / validIce.length;
    }
    if (validWaves.length > 0) {
      avgWave = validWaves.reduce((sum: number, w: any) => sum + w.env_conditions.wave_height, 0) / validWaves.length;
    }
  }

  const hasData = liveEnv != null;

  return (
    <section className="passage-overview-strip" aria-label="Passage Overview and Metrics">
      {/* Title block */}
      <div className="overview-title-cell">
        <span className="overview-heading">PASSAGE OVERVIEW</span>
        <span className="overview-sub">{hasData ? "Live Route Environmental Data" : "Waiting for route calculation..."}</span>
      </div>

      {/* Metric 1: Sea-ice concentration */}
      <div className="overview-metric-cell">
        <div className="metric-icon-circle">
          <svg width="24" height="24" viewBox="0 0 24 24" className="gauge-svg">
            <circle cx="12" cy="12" r="9" fill="none" stroke="#DCE5E5" strokeWidth="3" />
            <circle
              cx="12"
              cy="12"
              r="9"
              fill="none"
              stroke="#527C78"
              strokeWidth="3"
              strokeDasharray="56.5"
              strokeDashoffset={hasData ? 56.5 * (1 - avgIce) : 56.5}
              strokeLinecap="round"
              transform="rotate(-90 12 12)"
            />
          </svg>
        </div>
        <div className="metric-text-group">
          <span className="metric-large-num">{hasData ? `${Math.round(avgIce * 100)}%` : "--"}</span>
          <span className="metric-sub-label">sea-ice concentration</span>
        </div>
        <span className="metric-status-badge badge-mint">{hasData ? "LIVE" : "PENDING"}</span>
      </div>

      {/* Metric 2: Significant wave height */}
      <div className="overview-metric-cell">
        <div className="metric-icon-plain">
          <Waves size={16} className="icon-blue" />
        </div>
        <div className="metric-text-group">
          <span className="metric-large-num">{hasData ? `${avgWave.toFixed(1)} m` : "--"}</span>
          <span className="metric-sub-label">significant wave height</span>
        </div>
        <span className="metric-status-badge badge-blue">{hasData ? "LIVE" : "PENDING"}</span>
      </div>

      {/* Metric 3: Route risk score */}
      <div className="overview-metric-cell">
        <div className="metric-icon-plain">
          <ShieldAlert size={16} className={route ? "icon-amber" : "icon-slate"} />
        </div>
        <div className="metric-text-group">
          <span className="metric-large-num">{route ? riskScore.toFixed(2) : "--"}</span>
          <span className="metric-sub-label">route risk score</span>
        </div>
        <span className={`metric-status-badge ${route ? "badge-amber" : "badge-slate"}`}>{route ? "ACTIVE" : "PENDING"}</span>
      </div>

      {/* Metric 4: Data confidence */}
      <div className="overview-metric-cell">
        <div className="metric-icon-plain">
          <Shield size={16} className="icon-slate" />
        </div>
        <div className="metric-text-group">
          <span className="metric-large-num">{forecast.confidence}</span>
          <span className="metric-sub-label">data confidence</span>
        </div>
        <span className="metric-status-badge badge-slate">{forecast.horizonHours} H HORIZON</span>
      </div>
    </section>
  );
}

/** Format a date as "DD MMM" */
function fmtShort(date: Date) {
  const months = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
  ];
  return `${date.getDate()} ${months[date.getMonth()]}`;
}

/** Format a date as "DD Mon YYYY" */
function fmtLong(date: Date) {
  const months = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];
  return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
}

/** Format a date as "DD Mon YYYY · HH:MM UTC" for forecast datetime display */
export function fmtForecastDateTime(date: Date) {
  const months = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];
  const hh = String(date.getUTCHours()).padStart(2, "0");
  const mm = String(date.getUTCMinutes()).padStart(2, "0");
  return `${date.getUTCDate()} ${months[date.getUTCMonth()]} ${date.getUTCFullYear()} · ${hh}:${mm} UTC`;
}

export function Timeline({
  forecast,
  forecastHours,
  onForecastHoursChange,
  selectedDate,
  onDateChange,
}: {
  forecast: ForecastMeta;
  forecastHours: number;
  onForecastHoursChange: (hours: number) => void;
  selectedDate: Date;
  onDateChange: (date: Date) => void;
}) {
  const dateInputRef = useRef<HTMLInputElement>(null);

  // 5 tick dates matching Image 2: [12 SEP, 13 SEP - NOW, 14 SEP, 15 SEP, 16 SEP]
  const tickDates = Array.from({ length: 5 }, (_, i) => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + i - 1);
    return d;
  });

  const now = new Date();
  const isToday = (d: Date) => {
    return d.getUTCFullYear() === now.getUTCFullYear() &&
           d.getUTCMonth() === now.getUTCMonth() &&
           d.getUTCDate() === now.getUTCDate();
  };

  const fillPercent = Math.min(100, Math.max(0, (forecastHours / forecast.horizonHours) * 100));

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onForecastHoursChange(Number(e.target.value));
  };

  const handleDateClick = () => {
    dateInputRef.current?.showPicker?.();
    dateInputRef.current?.click();
  };

  const handleDateInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (val) {
      // Parse as UTC midnight so it round-trips correctly through
      // toISOString().split("T")[0] → the controlled `value` on re-render.
      // Using local midnight ("T00:00:00") would shift by the UTC offset
      // on toISOString(), causing the controlled input to snap back and
      // appear as if the selection was ignored.
      onDateChange(new Date(val + "T00:00:00Z"));
    }
  };

  const dateInputValue = selectedDate.toISOString().split("T")[0];

  return (
    <div className="time-control-bar" aria-label="Forecast Time Control">
      {/* Left: Play button + TIME CONTROL label */}
      <div className="time-control-left">
        <button type="button" className="time-play-btn" title="Play forecast timeline" aria-label="Play forecast">
          <Play size={10} fill="currentColor" />
        </button>
        <div className="time-control-label-group">
          <span className="time-control-title">TIME CONTROL</span>
          <span className="time-control-horizon">{forecast.horizonHours} h forecast</span>
        </div>
      </div>

      {/* Center: Ruler line and slider */}
      <div className="time-control-center">
        <div className="time-slider-track">
          <div className="time-slider-bg" />
          <div className="time-slider-progress" style={{ width: `${fillPercent}%` }} />
          <div className="time-slider-pin" style={{ left: `${fillPercent}%` }} />
          <input
            type="range"
            min={0}
            max={forecast.horizonHours}
            value={forecastHours}
            onChange={handleSliderChange}
            className="time-range-input"
            aria-label="Forecast hours slider"
          />
        </div>

        {/* Tick labels matching Image 2 */}
        <div className="time-ticks-row">
          {tickDates.map((d, i) => {
            const nowMatch = isToday(d);
            return (
              <span key={i} className={`time-tick-label ${nowMatch ? "is-now" : ""}`}>
                {nowMatch ? `${fmtShort(d)} · NOW` : fmtShort(d)}
              </span>
            );
          })}
        </div>
      </div>

      {/* Right: Date Button — displays computed forecast datetime (base date + slider hours) */}
      <button
        className="time-date-picker-btn"
        onClick={handleDateClick}
        type="button"
        title="Select baseline date"
      >
        <Calendar size={13} className="btn-calendar-icon" />
        <span>{fmtForecastDateTime(new Date(selectedDate.getTime() + forecastHours * 60 * 60 * 1000))}</span>
        <input
          ref={dateInputRef}
          type="date"
          value={dateInputValue}
          onChange={handleDateInputChange}
          className="date-input-hidden"
          tabIndex={-1}
        />
      </button>
    </div>
  );
}

export function MapOverlayLegend() {
  return (
    <div className="chart-analytical-legend" aria-label="Analytical Overlays Legend">
      <div className="legend-head-row">
        <span className="legend-head-title">ANALYTICAL OVERLAYS</span>
        <span className="legend-head-mode">LIVE VIEW</span>
      </div>

      <div className="legend-items-list">
        <div className="legend-item-row">
          <span className="legend-swatch ice-swatch" />
          <span className="legend-item-label">Sea-ice concentration</span>
          <span className="legend-item-val">0–100%</span>
        </div>

        <div className="legend-item-row">
          <span className="legend-swatch risk-hatched-swatch" />
          <span className="legend-item-label">Predicted risk</span>
          <span className="legend-item-val">Low — Avoid</span>
        </div>

        <div className="legend-item-row">
          <span className="legend-swatch forecast-dashed-swatch" />
          <span className="legend-item-label">Trajectory forecast</span>
          <span className="legend-item-val">72 h</span>
        </div>

        <div className="legend-item-row">
          <span className="legend-swatch iceberg-triangle-swatch">▲</span>
          <span className="legend-item-label">Observed icebergs</span>
          <span className="legend-item-val">Live data</span>
        </div>
      </div>
    </div>
  );
}

export function ForecastBadge({
  forecast,
  forecastDateTime,
}: {
  forecast: ForecastMeta;
  /** Computed forecast date+time string derived from selectedDate + forecastHours.
   *  When provided, replaces forecast.asOf for the displayed date portion. */
  forecastDateTime?: string;
}) {
  return (
    <div className="map-forecast-pill">
      <Satellite size={14} className="forecast-pill-icon" />
      <div className="forecast-pill-text">
        <strong className="forecast-pill-status">Forecast available</strong>
        <span className="forecast-pill-meta">
          {forecastDateTime ?? forecast.asOf} · {forecast.confidence} confidence
        </span>
      </div>
    </div>
  );
}
