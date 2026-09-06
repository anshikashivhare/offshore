"use client";

/**
 * MapLegend — display-only legend.
 *
 * Renders one row per layer registered in useLayerStore. The row is
 * dimmed when the layer is disabled but remains visible — this is a
 * legend, not a toggle. (An interactive layer panel is a separate
 * future component.)
 *
 * Re-renders are kept cheap: the component subscribes to the `enabled`
 * slice of state only, not the whole `layers` object, so toggling
 * opacity on one layer doesn't re-render the legend.
 */

import { useLayerStore } from "@/stores/use-layer-store";
import { LAYER_IDS, LAYER_META, type LayerId } from "@/lib/types/layer";

const SWATCH: Record<LayerId, string> = {
  seaIce: "linear-gradient(90deg, hsl(176 60% 70% / 0.5), hsl(165 80% 65% / 0.85))",
  icebergs: "hsl(195 30% 75%)",
  oceanCurrents: "hsl(210 70% 60%)",
  weather: "hsl(40 90% 60%)",
  risk: "hsl(0 75% 65%)",
  route: "hsl(190 80% 70%)",
  vessel: "hsl(0 0% 90%)",
};

export function MapLegend() {
  // Subscribe to the enabled slice only. Opacity changes won't
  // re-render this component.
  const enabled = useLayerStore((s) => {
    const out: Partial<Record<LayerId, boolean>> = {};
    for (const id of LAYER_IDS) out[id] = s.layers[id].enabled;
    return out;
  });

  return (
    <div
      className="panel absolute bottom-4 left-4 z-10 min-w-[220px] p-3 text-sm"
      role="region"
      aria-label="Map legend"
    >
      <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
        Layers
      </div>
      <ul className="space-y-1.5">
        {LAYER_IDS.map((id) => {
          const meta = LAYER_META[id];
          const isOn = enabled[id];
          return (
            <li
              key={id}
              className="flex items-center gap-2.5"
              style={{ opacity: isOn ? 1 : 0.45 }}
            >
              <span
                aria-hidden
                className="inline-block h-3 w-3 rounded-sm border border-[color:var(--border-subtle)]"
                style={{ background: SWATCH[id] }}
              />
              <div className="flex flex-col">
                <span className="text-[color:var(--fg-primary)] leading-tight">
                  {meta.label}
                </span>
                <span className="text-[11px] text-[color:var(--fg-muted)] leading-tight">
                  {meta.description}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
