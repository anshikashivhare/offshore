import { useRef } from "react";
import {
  Activity,
  CalendarDays,
  Clock3,
  CloudSnow,
  Database,
  Menu,
  Satellite,
  Waves,
} from "lucide-react";
import type { ForecastMeta } from "@/lib/offshore-types";

export function AppHeader({
  onMenu,
  routeLabel,
}: {
  onMenu: () => void;
  routeLabel?: string;
}) {
  return (
    <header className="app-header">
      <button
        className="mobile-menu"
        onClick={onMenu}
        aria-label="Open mission menu"
      >
        <Menu size={18} />
      </button>
      <div className="brand">
        <div className="brand-mark">
          <span />
          <span />
          <span />
        </div>
        <div>
          <strong>OFFSHORE</strong>
          <small>navigation intelligence</small>
        </div>
      </div>
      <div className="header-context">
        <span className="context-dot" /> Antarctic sector{" "}
        <b>{routeLabel || "Rothera → Casey"}</b>
        <span className="header-divider" />
        <span className="header-time">
          <Clock3 size={14} /> 13 SEP 2026 · 11:42 UTC
        </span>
      </div>
      <div className="header-actions">
        <div className="sync-status">
          <span />
          <div>
            <b>System nominal</b>
            <small>Last sync 04 min ago</small>
          </div>
        </div>
        <button className="avatar" aria-label="Open operator profile">
          OC
        </button>
      </div>
    </header>
  );
}

export function KpiStrip({ forecast }: { forecast: ForecastMeta }) {
  return (
    <div className="kpi-strip">
      <div className="kpi-heading">
        <span className="eyebrow">PASSAGE OVERVIEW</span>
        <span>Mock data · API schema ready</span>
      </div>
      <div className="kpi">
        <CloudSnow size={16} />
        <span>
          <b>42%</b>
          <small>sea-ice concentration</small>
        </span>
        <em className="status-pill mint">stable</em>
      </div>
      <div className="kpi">
        <Waves size={16} />
        <span>
          <b>0.8 m</b>
          <small>significant wave height</small>
        </span>
        <em className="status-pill blue">forecast</em>
      </div>
      <div className="kpi">
        <Activity size={16} />
        <span>
          <b>0.31</b>
          <small>route risk score</small>
        </span>
        <em className="status-pill amber">moderate</em>
      </div>
      <div className="kpi">
        <Database size={16} />
        <span>
          <b>{forecast.confidence}</b>
          <small>data confidence</small>
        </span>
        <em className="status-pill slate">72 h horizon</em>
      </div>
    </div>
  );
}

/** Format a date as "DD MMM" */
function fmtShort(date: Date) {
  const months = [
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
  ];
  return `${date.getDate()} ${months[date.getMonth()]}`;
}

/** Format a date as "DD Mon YYYY" */
function fmtLong(date: Date) {
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
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

  // Build tick dates from selectedDate: day before, day of, and 3 days after
  const tickDates = Array.from({ length: 5 }, (_, i) => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + i - 1);
    return d;
  });

  const fillPercent = (forecastHours / forecast.horizonHours) * 100;

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
      onDateChange(new Date(val + "T00:00:00"));
    }
  };

  // Format selected date for the date input value
  const dateInputValue = selectedDate.toISOString().split("T")[0];

  return (
    <div className="timeline">
      <div className="timeline-label">
        <CalendarDays size={14} />
        <span>TIME CONTROL</span>
        <b>{forecast.horizonHours} h forecast</b>
      </div>
      <div className="timeline-track">
        <div className="timeline-line">
          <span
            className="timeline-fill"
            style={{ width: `${fillPercent}%` }}
          />
          <i
            className="timeline-pin"
            style={{ left: `${fillPercent}%` }}
          />
          <input
            type="range"
            min={0}
            max={forecast.horizonHours}
            value={forecastHours}
            onChange={handleSliderChange}
            className="timeline-slider"
            aria-label="Forecast time"
          />
        </div>
        <div className="timeline-ticks">
          {tickDates.map((d, i) => (
            <span
              key={i}
              className={i === 1 ? "active" : ""}
            >
              {i === 1 ? `${fmtShort(d)} · NOW` : fmtShort(d)}
            </span>
          ))}
        </div>
      </div>
      <button
        className="timeline-select"
        onClick={handleDateClick}
        type="button"
      >
        <CalendarDays size={13} />
        {fmtLong(selectedDate)}
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
    <div className="map-legend">
      <div className="legend-head">
        <span>ANALYTICAL OVERLAYS</span>
        <small>LIVE VIEW</small>
      </div>
      <div className="legend-row">
        <i className="gradient-ice" />
        <span>Sea-ice concentration</span>
        <b>0–100%</b>
      </div>
      <div className="legend-row">
        <i className="risk-dots" />
        <span>Predicted risk</span>
        <b>LOW · AVOID</b>
      </div>
      <div className="legend-row">
        <i className="line-predicted" />
        <span>Trajectory forecast</span>
        <b>72 h</b>
      </div>
    </div>
  );
}

export function ForecastBadge({ forecast }: { forecast: ForecastMeta }) {
  return (
    <div className="forecast-badge">
      <Satellite size={14} />
      <span>
        <b>Forecast available</b>
        <small>
          {forecast.asOf} · {forecast.confidence} confidence
        </small>
      </span>
    </div>
  );
}
