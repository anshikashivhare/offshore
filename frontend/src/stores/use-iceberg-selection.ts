/**
 * useIcebergSelection — minimal selection state for the iceberg layer.
 *
 * Intentionally a separate store from useLayerStore: layer-store
 * concerns are global (visibility/opacity); selection is per-feature
 * UX. Splitting them keeps the layer store generic and reusable for
 * future layers (risk-feature selection, route-stop selection, etc.)
 * without forcing every consumer to know about iceberg specifics.
 */
"use client";

import { create } from "zustand";

interface IcebergSelectionState {
  selectedId: string | null;
  select: (id: string | null) => void;
  clear: () => void;
}

export const useIcebergSelection = create<IcebergSelectionState>((set) => ({
  selectedId: null,
  select: (id) => set({ selectedId: id }),
  clear: () => set({ selectedId: null }),
}));
