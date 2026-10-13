import type { RasterLayerSpecification } from "maplibre-gl";
import { GEBCO_LAYER_ID } from "./gebco";
import {
  SEA_ICE_LAYER_ID,
  SEA_ICE_SOURCE_ID,
  getSeaIceLayerConfig,
  getSeaIceSourceConfig,
  getSeaIceTileUrl,
  resolveAvailableSeaIce,
  type SeaIceDateMode,
  type SeaIceSelection,
} from "./nasaGibs";

export type SeaIceLoadStatus = "loading" | "loaded" | "error" | "hidden";
export type SeaIceLayerState = {
  selection: SeaIceSelection | null;
  status: SeaIceLoadStatus;
  message?: string;
};

type TileEventData = {
  state?: string;
  aborted?: boolean;
  texture?: unknown;
  tileID?: { key?: string | number };
};

export type SeaIceMapEvent = {
  type?: string;
  sourceId?: string;
  source?: { tiles?: string[] };
  isSourceLoaded?: boolean;
  sourceDataType?: string;
  tile?: TileEventData;
  error?: { name?: string; message?: string };
};

/** The public MapLibre operations used here, kept small for headless lifecycle tests. */
export interface SeaIceMap {
  getSource(id: string): unknown;
  getLayer(id: string): unknown;
  getStyle(): { layers?: { id: string; type: string }[] };
  addSource(id: string, source: ReturnType<typeof getSeaIceSourceConfig>): unknown;
  addLayer(layer: RasterLayerSpecification, before?: string): unknown;
  removeLayer(id: string): unknown;
  removeSource(id: string): unknown;
  setPaintProperty(id: string, property: string, value: number): unknown;
  setLayoutProperty(id: string, property: string, value: string): unknown;
  isSourceLoaded(id: string): boolean;
  on(event: "sourcedata" | "sourcedataloading" | "error" | "style.load", listener: (event: SeaIceMapEvent) => void): unknown;
  off(event: "sourcedata" | "sourcedataloading" | "error" | "style.load", listener: (event: SeaIceMapEvent) => void): unknown;
}

type LayerOptions = { selection: SeaIceSelection | null; visible: boolean; opacity: number };

export type SeaIceAvailabilityState = {
  selection: SeaIceSelection | null;
  status: "loading" | "ready" | "error";
  message?: string;
};

/** One owner for metadata resolution, with one retry and harmless late results. */
export function requestSeaIceAvailability(
  mode: SeaIceDateMode,
  customDate: string | undefined,
  onState: (state: SeaIceAvailabilityState) => void,
  resolve = resolveAvailableSeaIce,
) {
  let cancelled = false;
  let finished = false;
  let attempt = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const run = () => {
    if (cancelled || finished) return;
    attempt++;
    onState({ selection: null, status: "loading", message: attempt > 1 ? "Rechecking NASA GIBS availability…" : undefined });
    timer = setTimeout(() => {
      if (cancelled || finished) return;
      finished = true;
      onState({ selection: null, status: "error", message: "NASA GIBS availability check timed out. Recheck to try again." });
    }, 12000);
    Promise.resolve().then(() => cancelled || finished ? null : resolve(mode, customDate)).then((selection) => {
      if (cancelled || finished || !selection) return;
      globalThis.clearTimeout(timer);
      finished = true;
      onState({ selection, status: "ready" });
    }, (error: unknown) => {
      if (cancelled || finished) return;
      globalThis.clearTimeout(timer);
      if (attempt < 2) {
        onState({ selection: null, status: "loading", message: "NASA GIBS availability check failed; retrying once…" });
        timer = setTimeout(run, 1500);
      } else {
        finished = true;
        const detail = error instanceof Error ? ` ${error.message}` : "";
        onState({ selection: null, status: "error", message: `NASA GIBS sea-ice availability unavailable.${detail}` });
      }
    });
  };
  run();
  return () => {
    cancelled = true;
    globalThis.clearTimeout(timer);
  };
}

export function getSeaIceSnapshotNote(selection: SeaIceSelection, mode: SeaIceDateMode): string {
  const requested = selection.requestedDate && selection.requestedDate !== selection.date
    ? ` · requested ${selection.requestedDate}`
    : "";
  if (mode === "custom") {
    return `Historical snapshot${selection.stale ? " · stale snapshot" : ""}${requested}`;
  }
  if (selection.stale) return `Stale snapshot${mode === "latest" ? " · latest available" : ""}${requested}`;
  return requested ? `Nearest available snapshot${requested}` : "";
}

/** Owns only the sea-ice source/layer and listeners, never the rest of the map. */
export function createSeaIceLayerController(
  map: SeaIceMap,
  initial: LayerOptions,
  onStatus: (state: SeaIceLayerState) => void,
) {
  let options = initial;
  let disposed = false;
  let generation = 0;
  let ownedSource: unknown;
  let sourceKey = "";
  let sawTileSuccess = false;
  let sourceError = false;
  let successAfterError = false;
  const failedTiles = new globalThis.Map<unknown, TileEventData>();
  let status: SeaIceLoadStatus = "loading";
  let message: string | undefined;
  let timeout: ReturnType<typeof setTimeout> | undefined;
  let removeDataListeners = () => {};

  const clearTimeout = () => {
    if (timeout !== undefined) globalThis.clearTimeout(timeout);
    timeout = undefined;
  };
  const publish = (next: SeaIceLoadStatus, detail?: string) => {
    if (disposed) return;
    status = next;
    message = detail;
    if (!options.visible || next !== "loading") clearTimeout();
    onStatus({ selection: options.selection, status: options.visible ? next : "hidden", message: detail });
    if (options.visible && next === "loading" && options.selection && timeout === undefined) {
      const currentGeneration = generation;
      timeout = setTimeout(() => {
        if (!disposed && generation === currentGeneration) {
          sourceError = true;
          successAfterError = false;
          publish("error", "Sea-ice tiles did not finish loading. Recheck availability.");
        }
      }, 20000);
    }
  };
  const currentSource = () => Boolean(ownedSource) && map.getSource(SEA_ICE_SOURCE_ID) === ownedSource;
  const isComplete = () => {
    try { return currentSource() && map.isSourceLoaded(SEA_ICE_SOURCE_ID); }
    catch { return false; }
  };
  const removeOwnedSource = () => {
    try {
      if (currentSource()) {
        if (map.getLayer(SEA_ICE_LAYER_ID)) map.removeLayer(SEA_ICE_LAYER_ID);
        map.removeSource(SEA_ICE_SOURCE_ID);
      }
    } catch {
      // A style swap or map teardown may already have removed both objects.
    }
    ownedSource = undefined;
  };
  const applyDisplay = () => {
    if (!currentSource() || !map.getLayer(SEA_ICE_LAYER_ID)) return;
    map.setPaintProperty(SEA_ICE_LAYER_ID, "raster-opacity", options.opacity);
    map.setLayoutProperty(SEA_ICE_LAYER_ID, "visibility", options.visible ? "visible" : "none");
  };
  const refreshStatus = () => {
    failedTiles.forEach((tile, key) => {
      if (tile.aborted || tile.state === "unloaded" || (tile.state === "loaded" && tile.texture)) failedTiles.delete(key);
    });
    if (sourceError || failedTiles.size) {
      publish("error", "Sea-ice tiles temporarily unavailable. Recheck or wait for recovery.");
    } else if (sawTileSuccess && isComplete()) {
      publish("loaded");
    } else {
      publish("loading");
    }
  };
  const install = () => {
    if (disposed) return;
    const currentGeneration = ++generation;
    clearTimeout();
    removeDataListeners();
    removeOwnedSource();
    sawTileSuccess = false;
    sourceError = false;
    successAfterError = false;
    failedTiles.clear();
    const selection = options.selection;
    sourceKey = selection ? JSON.stringify(getSeaIceSourceConfig(selection.date, selection)) : "";
    publish("loading");
    if (!selection) return;

    const tileUrl = getSeaIceTileUrl(selection.date, selection);
    const matches = (event: SeaIceMapEvent) => !disposed && generation === currentGeneration && currentSource() &&
      event.sourceId === SEA_ICE_SOURCE_ID && (!event.source?.tiles || event.source.tiles.includes(tileUrl));
    const onError = (event: SeaIceMapEvent) => {
      if (!matches(event) || event.error?.name === "AbortError" || event.tile?.aborted) return;
      successAfterError = false;
      if (event.tile) failedTiles.set(event.tile.tileID?.key ?? event.tile, event.tile);
      else sourceError = true;
      refreshStatus();
    };
    const onData = (event: SeaIceMapEvent) => {
      if (!matches(event)) return;
      // Metadata, visibility and empty events do not prove any raster imagery loaded.
      if (event.tile?.state === "loaded" && event.tile.texture && !event.tile.aborted) {
        sawTileSuccess = true;
        successAfterError = true;
        failedTiles.delete(event.tile.tileID?.key ?? event.tile);
      }
      if (successAfterError && isComplete()) sourceError = false;
      refreshStatus();
    };
    const onLoading = (event: SeaIceMapEvent) => {
      if (matches(event) && status !== "error") publish("loading");
    };
    map.on("error", onError);
    map.on("sourcedata", onData);
    map.on("sourcedataloading", onLoading);
    removeDataListeners = () => {
      map.off("error", onError);
      map.off("sourcedata", onData);
      map.off("sourcedataloading", onLoading);
    };
    try {
      map.addSource(SEA_ICE_SOURCE_ID, getSeaIceSourceConfig(selection.date, selection));
      ownedSource = map.getSource(SEA_ICE_SOURCE_ID);
      const before = map.getStyle().layers?.find((layer) =>
        layer.id !== "background" && layer.id !== GEBCO_LAYER_ID && layer.id !== SEA_ICE_LAYER_ID,
      )?.id;
      const layer = getSeaIceLayerConfig(options.opacity);
      map.addLayer({ ...layer, layout: { visibility: options.visible ? "visible" : "none" } }, before);
      applyDisplay();
      // Wait for actual tile success; addSource/addLayer alone is not a loaded state.
    } catch {
      sourceError = true;
      successAfterError = false;
      publish("error", "Sea-ice overlay could not be initialized. Recheck availability.");
    }
  };
  map.on("style.load", install);
  install();

  return {
    update(next: LayerOptions) {
      if (disposed) return;
      const nextSourceKey = next.selection ? JSON.stringify(getSeaIceSourceConfig(next.selection.date, next.selection)) : "";
      const visibilityChanged = options.visible !== next.visible;
      options = next;
      if (nextSourceKey !== sourceKey) install();
      else {
        try { applyDisplay(); }
        catch {
          sourceError = true;
          successAfterError = false;
          publish("error", "Sea-ice overlay could not be updated. Recheck availability.");
          return;
        }
        if (visibilityChanged) refreshStatus();
        else onStatus({ selection: options.selection, status: options.visible ? status : "hidden", message });
      }
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      generation++;
      clearTimeout();
      map.off("style.load", install);
      removeDataListeners();
      removeOwnedSource();
    },
  };
}
