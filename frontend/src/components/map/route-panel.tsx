"use client";

import { useLayerStore } from "@/stores/use-layer-store";
import { useRouteStore } from "@/stores/use-route-store";
import { VESSEL_SPEED_KNOTS } from "@/lib/routing/a-star-router";
import { RouteRiskChart } from "./route-risk-chart";
import { useReverseGeocode } from "@/lib/hooks/use-reverse-geocode";
import { PortDropdown } from "./port-dropdown";

interface Props {
  enabled: boolean;
}

export function RoutePanel({ enabled }: Props) {
  const status = useRouteStore((s) => s.status);
  const result = useRouteStore((s) => s.result);
  const recalculate = useRouteStore((s) => s.recalculate);
  const origin = useRouteStore((s) => s.origin);
  const destination = useRouteStore((s) => s.destination);
  const pendingSelection = useRouteStore((s) => s.pendingSelection);
  const setPendingSelection = useRouteStore((s) => s.setPendingSelection);
  const setEndpoints = useRouteStore((s) => s.setEndpoints);
  const toggle = useLayerStore((s) => s.toggle);
  
  const originName = useReverseGeocode(origin);
  const destName = useReverseGeocode(destination);

  return (
    <div
      className="panel absolute top-20 right-4 z-10 w-[260px] p-3 text-sm"
      role="region"
      aria-label="Planned route panel"
      style={{ opacity: enabled ? 1 : 0.55 }}
    >
      {/* Header */}
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
          Planned route
        </span>
        <Toggle
          checked={enabled}
          onChange={() => toggle("route")}
          accentVar="--accent-route"
        />
      </div>

      <div
        className="mb-3 flex items-center gap-1.5 text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]"
        aria-label="Data source notice"
      >
        <span
          aria-hidden
          className="inline-block h-1.5 w-1.5 rounded-full"
          style={{ background: "var(--fg-muted)" }}
        />
        Mock data — placeholder
      </div>

      {/* Origin/Destination Map Clicks */}
      <div className="mb-3 space-y-2">
        <PortDropdown
          label="Origin"
          type="origin"
          currentName={originName}
          lat={origin.lat}
          lon={origin.lon}
        />
        <PortDropdown
          label="Destination"
          type="destination"
          currentName={destName}
          lat={destination.lat}
          lon={destination.lon}
        />
        
        <button
          onClick={() => {
            setEndpoints({ lat: -45, lon: -60 }, { lat: -45, lon: -60 });
          }}
          className="w-full text-[10px] uppercase tracking-wider py-1 border border-dashed border-[color:var(--border-subtle)] text-[color:var(--fg-muted)] hover:text-[color:var(--fg-primary)] hover:border-[color:var(--fg-primary)] transition-colors rounded"
        >
          Clear Selection
        </button>
      </div>

      {/* Status */}
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
          Status
        </span>
        <span
          className="text-[11px] font-mono uppercase tracking-[0.08em]"
          style={{ color: statusColor(status) }}
        >
          {statusLabel(status)}
        </span>
      </div>

      {/* Distance (the headline number) */}
      <div className="mb-1">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
          Distance
        </div>
        <div
          className="text-2xl font-mono font-semibold leading-tight"
          style={{ color: "var(--accent-route)" }}
        >
          {result ? `${result.totalNm.toLocaleString(undefined, { maximumFractionDigits: 0 })} NM` : "—"}
        </div>
      </div>

      {/* Time */}
      <div className="mb-2">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
          Time en route
        </div>
        <div className="text-sm text-[color:var(--fg-secondary)] font-mono">
          {result
            ? `${formatDuration(result.hours)} @ ${VESSEL_SPEED_KNOTS} kn`
            : "—"}
        </div>
      </div>

      {/* Risk badge */}
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
          Risk level
        </span>
        {result ? <RiskBadge score={result.maxRiskScore} /> : (
          <span className="text-[11px] font-mono text-[color:var(--fg-muted)]">—</span>
        )}
      </div>

      {/* Re-calculate button */}
      <button
        type="button"
        onClick={recalculate}
        disabled={status === "calculating"}
        className="w-full px-3 py-1.5 rounded-sm text-[11px] font-medium uppercase tracking-[0.08em] transition-colors disabled:cursor-not-allowed disabled:opacity-50"
        style={{
          background: "var(--accent-route)",
          color: "var(--bg-app)",

        }}
        onMouseEnter={(e) => {
          if (status !== "calculating") {
            e.currentTarget.style.filter = "brightness(1.1)";
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.filter = "none";
        }}
        aria-label="Re-calculate route"
      >
        {status === "calculating" ? "Calculating…" : "Re-calculate"}
      </button>

      {/* Risk Profile Graph */}
      <RouteRiskChart />
    </div>
  );
}

/* ------------------------------------------------------------------
 * Subcomponents (kept local — they're panel-specific)
 * ------------------------------------------------------------------ */

function RiskBadge({ score }: { score: number }) {
  // Thresholds chosen so:
  //   - < 30   → "Low"  (a 0.5 ice + 0.5 iceberg edge is 40 + 30 = 70 → Moderate, so
  //                     anything below 30 is "free" passage)
  //   - < 70   → "Moderate" (single-hazard edges, e.g. crossing 0.5 ice without icebergs)
  //   - ≥ 70   → "Severe" (multiple hazards stacked: dense ice + nearby iceberg)
  const tier: "low" | "moderate" | "severe" =
    score < 30 ? "low" : score < 70 ? "moderate" : "severe";
  const colors = {
    low:      { bg: "rgba(94, 234, 212, 0.18)",  fg: "var(--status-safe)"   },  // signal teal
    moderate: { bg: "rgba(251, 191, 36, 0.18)",  fg: "var(--status-warn)"   },  // alert amber
    severe:   { bg: "rgba(248, 113, 113, 0.18)", fg: "var(--status-danger)" },  // hazard red
  }[tier];
  const label = tier === "low" ? "Low" : tier === "moderate" ? "Moderate" : "Severe";
  return (
    <span
      className="rounded-full px-2 py-0.5 text-[10px] uppercase tracking-[0.08em] font-medium"
      style={{ background: colors.bg, color: colors.fg }}
      aria-label={`Risk level: ${label} (score ${score.toFixed(0)})`}
    >
      {label}
    </span>
  );
}

function Toggle({
  checked,
  onChange,
  accentVar,
}: {
  checked: boolean;
  onChange: () => void;
  /** CSS variable for the on-state color. Defaults to --accent;
   *  the route panel passes --accent-route. */
  accentVar?: string;
}) {
  const onBg = accentVar ? `var(${accentVar})` : "var(--accent)";
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className="relative h-4 w-7 rounded-full border border-[color:var(--border-subtle)] transition-colors"
      style={{ background: checked ? onBg : "var(--color-fog)" }}
    >
      <span
        className="absolute top-[1px] h-2.5 w-2.5 rounded-full transition-all"
        style={{
          left: checked ? "calc(100% - 11px)" : "1px",
          background: "var(--fg-primary)",
        }}
      />
    </button>
  );
}

/* ------------------------------------------------------------------
 * Helpers
 * ------------------------------------------------------------------ */

function statusLabel(status: "idle" | "calculating" | "ready"): string {
  if (status === "idle") return "Idle";
  if (status === "calculating") return "Calculating…";
  return "Ready";
}

function statusColor(status: "idle" | "calculating" | "ready"): string {
  // Status colors are deliberately muted (--fg-muted, --accent,
  // --status-safe) so the row reads as a status badge, not an
  // alert. The user knows the route is computed; this is just
  // telling them which phase it's in.
  if (status === "idle") return "var(--fg-muted)";
  if (status === "calculating") return "var(--accent-route)";
  return "var(--status-safe)";
}

/** Convert hours to "X.X days" / "Y h" depending on magnitude. */
function formatDuration(hours: number): string {
  if (hours >= 24) {
    return `${(hours / 24).toFixed(1)} days`;
  }
  return `${hours.toFixed(1)} h`;
}
