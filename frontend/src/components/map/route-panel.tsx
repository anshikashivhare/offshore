"use client";

/**
 * RoutePanel
 * ----------
 * HUD panel pinned to the top-right of the map, below the
 * maplibre navigation zoom controls.
 *
 * Contents:
 *   - Header: "Planned route" + a layer toggle.
 *   - Mock-data notice: a small dot + "Mock data — placeholder"
 *     label. Same pattern as the ocean-current panel. The route
 *     is computed from the same placeholder sea-ice and iceberg
 *     sets; the label is honest about that.
 *   - Status row: idle / calculating… / ready.
 *   - Distance: large cyan number, formatted with thousands
 *     separators ("1,840 NM").
 *   - Time: smaller secondary line, e.g. "5.5 days @ 14 kn".
 *   - Risk badge: color-coded chip (Low / Moderate / Severe)
 *     driven by the route's maxRiskScore.
 *   - Re-calculate button: triggers useRouteStore.recalculate().
 *
 * Visual consistency with the rest of the dashboard:
 *   - Same `panel` class as MapLegend / ocean-current panel.
 *   - Same 10px / tracking-[0.16em] uppercase header typography.
 *   - Same `--accent-route` color token for the route number
 *     and the recalculate button.
 *
 * Dim-when-disabled:
 *   When the user toggles the layer off, the panel's opacity
 *   drops to 0.55 (same as the ocean-current panel). The
 *   metrics stay readable so the user can still see the
 *   previously-computed route at a glance.
 */

import { useLayerStore } from "@/stores/use-layer-store";
import { useRouteStore } from "@/stores/use-route-store";
import { VESSEL_SPEED_KNOTS } from "@/lib/routing/a-star-router";

interface Props {
  enabled: boolean;
}

export function RoutePanel({ enabled }: Props) {
  const status = useRouteStore((s) => s.status);
  const result = useRouteStore((s) => s.result);
  const recalculate = useRouteStore((s) => s.recalculate);
  const toggle = useLayerStore((s) => s.toggle);

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

      {/* Mock-data notice — same pattern as the ocean-current
          panel: a small dot + a muted uppercase label. The
          color is --fg-muted (not --status-warn) so it reads as
          a metadata note rather than an alert. */}
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
            e.currentTarget.style.background = "var(--accent-route-hover)";
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "var(--accent-route)";
        }}
        aria-label="Re-calculate route"
      >
        {status === "calculating" ? "Calculating…" : "Re-calculate route"}
      </button>
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
