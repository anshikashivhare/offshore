/**
 * useLayerStore — single source of truth for layer visibility/opacity.
 *
 * Architectural decisions:
 *   - Zustand (not React Context) so that the maplibre adapter can read
 *     state imperatively without prop-drilling and without re-rendering
 *     the entire map component tree on every toggle.
 *   - Per-layer entry keyed by LayerId (not a free-form object) so we
 *     can statically enforce which layers exist.
 *   - `enabled` defaults to LAYER_META[id].defaultEnabled — but the
 *     store holds its own copy. This is deliberate: user overrides
 *     (e.g. layer panel UI) shouldn't mutate the LAYER_META module
 *     export.
 */
"use client";

import { create } from "zustand";
import {
  DEFAULT_LAYER_STATE,
  LAYER_IDS,
  LAYER_META,
  type LayerId,
  type LayerState,
} from "@/lib/types/layer";

type LayerMap = Record<LayerId, LayerState>;

function initialMap(): LayerMap {
  const m = {} as LayerMap;
  for (const id of LAYER_IDS) {
    m[id] = {
      enabled: LAYER_META[id].defaultEnabled,
      opacity: DEFAULT_LAYER_STATE.opacity,
    };
  }
  return m;
}

interface LayerStore {
  layers: LayerMap;
  toggle: (id: LayerId) => void;
  setEnabled: (id: LayerId, enabled: boolean) => void;
  setOpacity: (id: LayerId, opacity: number) => void;
  get: (id: LayerId) => LayerState;
}

export const useLayerStore = create<LayerStore>((set, get) => ({
  layers: initialMap(),
  toggle: (id) =>
    set((s) => ({
      layers: {
        ...s.layers,
        [id]: { ...s.layers[id], enabled: !s.layers[id].enabled },
      },
    })),
  setEnabled: (id, enabled) =>
    set((s) => ({
      layers: { ...s.layers, [id]: { ...s.layers[id], enabled } },
    })),
  setOpacity: (id, opacity) =>
    set((s) => ({
      layers: {
        ...s.layers,
        [id]: { ...s.layers[id], opacity: clamp01(opacity) },
      },
    })),
  get: (id) => get().layers[id],
}));

function clamp01(n: number): number {
  if (Number.isNaN(n)) return 0;
  if (n < 0) return 0;
  if (n > 1) return 1;
  return n;
}
