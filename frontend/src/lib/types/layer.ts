/**
 * Layer taxonomy for Offshore.
 *
 * Sourced from the SRS environmental / hazard / navigation layer split
 * (PS 26059). Only `seaIce` and `icebergs` have working implementations
 * today; the rest are reserved for future phases and exist as store
 * placeholders so the legend / layer-toggle UI can grow without a
 * store migration.
 *
 * Convention: string-literal union, NOT TypeScript enum, because
 * (a) it tree-shakes cleanly and (b) it serializes losslessly over
 * devtools / future wire APIs.
 */
export type LayerId =
  | "seaIce"
  | "icebergs"
  | "oceanCurrents"
  | "weather"
  | "risk"
  | "route"
  | "vessel";

export const LAYER_IDS: readonly LayerId[] = [
  "seaIce",
  "icebergs",
  "oceanCurrents",
  "weather",
  "risk",
  "route",
  "vessel",
] as const;

/** Per-layer UI/runtime state kept in the store. */
export interface LayerState {
  enabled: boolean;
  /** 0..1; applied to the maplibre layer's paint opacity. */
  opacity: number;
}

/** Default state for a single layer. Used to seed the store. */
export const DEFAULT_LAYER_STATE: LayerState = {
  enabled: false,
  opacity: 0.8,
};

/** Human-readable metadata for the legend. Kept here so legend & store
 *  can't drift — one source of truth per LayerId. */
export const LAYER_META: Record<
  LayerId,
  { label: string; description: string; defaultEnabled: boolean }
> = {
  seaIce: {
    label: "Sea-ice concentration",
    description: "Concentration gradient from open water to pack ice.",
    defaultEnabled: true,
  },
  icebergs: {
    label: "Iceberg detections",
    description: "Individual detection points from satellite / CV pipeline.",
    defaultEnabled: true,
  },
  oceanCurrents: {
    label: "Ocean currents",
    description: "Surface current vector field.",
    defaultEnabled: true,
  },
  weather: {
    label: "Weather",
    description: "Wind, pressure, sea state.",
    defaultEnabled: false,
  },
  risk: {
    label: "Maritime risk",
    description: "Composite risk surface from risk_engine.",
    defaultEnabled: false,
  },
  route: {
    label: "Planned route",
    description: "A* route output.",
    defaultEnabled: false,
  },
  vessel: {
    label: "Vessels",
    description: "AIS vessel positions.",
    defaultEnabled: false,
  },
};
