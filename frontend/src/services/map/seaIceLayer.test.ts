import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { RasterLayerSpecification } from "maplibre-gl";
import { GEBCO_LAYER_ID } from "./gebco";
import {
  SEA_ICE_SOURCE_ID,
  SEA_ICE_LAYER_ID,
  getSeaIceSourceConfig,
  getSeaIceTileUrl,
  type SeaIceSelection,
} from "./nasaGibs";
import {
  createSeaIceLayerController,
  getSeaIceSnapshotNote,
  requestSeaIceAvailability,
  type SeaIceAvailabilityState,
  type SeaIceLayerState,
  type SeaIceMap,
  type SeaIceMapEvent,
} from "./seaIceLayer";

type EventName = Parameters<SeaIceMap["on"]>[0];
type Listener = (event: SeaIceMapEvent) => void;
type FakeLayer = {
  id: string; type: string; source?: string;
  paint?: Record<string, unknown>; layout?: Record<string, unknown>;
};

class FakeMap implements SeaIceMap {
  sources = new Map<string, ReturnType<typeof getSeaIceSourceConfig>>();
  layers: FakeLayer[] = [
    { id: "background", type: "background" },
    { id: GEBCO_LAYER_ID, type: "raster" },
    { id: "route", type: "line" },
  ];
  listeners = new Map<EventName, Set<Listener>>();
  sourceLoaded = false;
  addedSources: ReturnType<typeof getSeaIceSourceConfig>[] = [];
  removed: string[] = [];

  getSource(id: string) { return this.sources.get(id); }
  getLayer(id: string) { return this.layers.find((layer) => layer.id === id); }
  getStyle() { return { layers: this.layers }; }
  addSource(id: string, source: ReturnType<typeof getSeaIceSourceConfig>) {
    if (this.sources.has(id)) throw new Error("duplicate source");
    const copy = { ...source, tiles: [...source.tiles] };
    this.sources.set(id, copy);
    this.addedSources.push(copy);
    this.sourceLoaded = false;
  }
  addLayer(layer: RasterLayerSpecification, before?: string) {
    const index = before ? this.layers.findIndex((entry) => entry.id === before) : this.layers.length;
    this.layers.splice(index, 0, { ...layer, paint: { ...layer.paint }, layout: { ...layer.layout } });
  }
  removeLayer(id: string) {
    this.removed.push(id);
    this.layers = this.layers.filter((layer) => layer.id !== id);
  }
  removeSource(id: string) { this.removed.push(id); this.sources.delete(id); }
  setPaintProperty(id: string, property: string, value: number) {
    const layer = this.getLayer(id)!;
    layer.paint = { ...layer.paint, [property]: value };
  }
  setLayoutProperty(id: string, property: string, value: string) {
    const layer = this.getLayer(id)!;
    layer.layout = { ...layer.layout, [property]: value };
  }
  isSourceLoaded() { return this.sourceLoaded; }
  on(name: EventName, listener: Listener) {
    if (!this.listeners.has(name)) this.listeners.set(name, new Set());
    this.listeners.get(name)!.add(listener);
  }
  off(name: EventName, listener: Listener) { this.listeners.get(name)?.delete(listener); }
  emit(name: EventName, event: SeaIceMapEvent = {}) {
    [...this.listeners.get(name) ?? []].forEach((listener) => listener(event));
  }
  event(extra: SeaIceMapEvent = {}): SeaIceMapEvent {
    return { sourceId: SEA_ICE_SOURCE_ID, source: this.getSource(SEA_ICE_SOURCE_ID), ...extra };
  }
  success(key = "tile", complete = true) {
    this.sourceLoaded = complete;
    this.emit("sourcedata", this.event({
      isSourceLoaded: complete,
      tile: { state: "loaded", texture: {}, tileID: { key } },
    }));
  }
  failure(key: string) {
    this.emit("error", this.event({
      tile: { state: "errored", tileID: { key } }, error: new Error("network failed"),
    }));
  }
}

const primary: SeaIceSelection = {
  productId: "AMSRU2_Sea_Ice_Concentration_12km",
  label: "AMSR-U2 Sea Ice Concentration 12km",
  date: "2025-09-01",
  tileMatrixSet: "GoogleMapsCompatible_Level6",
  maxZoom: 6,
  attribution: "NASA GIBS — AMSR-U2",
  stale: true,
};
const fallback: SeaIceSelection = {
  productId: "GHRSST_L4_MUR_Sea_Ice_Concentration",
  label: "GHRSST MUR Sea Ice Concentration",
  date: "2026-10-08",
  tileMatrixSet: "GoogleMapsCompatible_Level7",
  maxZoom: 7,
  attribution: "NASA GIBS — GHRSST MUR",
  stale: false,
};

const cleanups: (() => void)[] = [];
beforeEach(() => { vi.useFakeTimers(); });
afterEach(() => {
  cleanups.splice(0).forEach((cleanup) => cleanup());
  vi.useRealTimers();
});

function setup(selection: SeaIceSelection | null = fallback, visible = true, opacity = 0.55) {
  const map = new FakeMap();
  const states: SeaIceLayerState[] = [];
  const controller = createSeaIceLayerController(map, { selection, visible, opacity }, (state) => states.push(state));
  cleanups.push(controller.dispose);
  return { map, controller, states, latest: () => states[states.length - 1] };
}

describe("sea-ice raster lifecycle", () => {
  it("never adds guessed data and stays loading until actual tiles and source completion", () => {
    const { map, controller, latest } = setup(null);
    expect(map.addedSources).toHaveLength(0);
    expect(latest()).toMatchObject({ selection: null, status: "loading" });
    controller.update({ selection: fallback, visible: true, opacity: 0.55 });
    expect(map.getSource(SEA_ICE_SOURCE_ID)).toEqual(getSeaIceSourceConfig(fallback.date, fallback));
    expect(latest().status).toBe("loading");
    map.sourceLoaded = true;
    map.emit("sourcedata", map.event({ sourceDataType: "metadata", isSourceLoaded: true }));
    map.emit("sourcedata", map.event({ sourceDataType: "visibility", isSourceLoaded: true }));
    map.emit("sourcedata", map.event({ sourceDataType: "idle", isSourceLoaded: true }));
    map.emit("sourcedata", map.event({ tile: { state: "loaded" }, isSourceLoaded: true }));
    expect(latest().status).toBe("loading");
    map.success("tile", false);
    expect(latest().status).toBe("loading");
    map.sourceLoaded = true;
    map.emit("sourcedata", map.event({ sourceDataType: "idle", isSourceLoaded: true }));
    expect(latest()).toMatchObject({ selection: fallback, status: "loaded", message: undefined });
  });

  it("ignores unrelated errors and aborts, and clears a transient source error only after real recovery", () => {
    const { map, latest } = setup();
    map.success();
    map.emit("error", { sourceId: "ports", error: new Error("port failure") });
    map.emit("error", { error: new Error("basemap failure") });
    map.emit("error", map.event({ error: { name: "AbortError" } }));
    map.emit("error", map.event({ tile: { aborted: true }, error: new Error("cancelled") }));
    expect(latest().status).toBe("loaded");
    map.emit("error", map.event({ error: new Error("NASA temporarily unreachable") }));
    expect(latest().status).toBe("error");
    map.emit("sourcedata", { sourceId: "ports", isSourceLoaded: true });
    map.emit("sourcedata", map.event({ sourceDataType: "metadata", isSourceLoaded: true }));
    map.emit("sourcedata", map.event({ isSourceLoaded: true }));
    expect(latest().status).toBe("error");
    map.success("recovered", false);
    expect(latest().status).toBe("error");
    map.sourceLoaded = true;
    map.emit("sourcedata", map.event({ sourceDataType: "idle", isSourceLoaded: true }));
    expect(latest()).toMatchObject({ status: "loaded", message: undefined });
  });

  it("does not let one successful or empty tile event hide another still-failing tile", () => {
    const { map, latest } = setup();
    map.failure("a");
    map.failure("b");
    map.success("unrelated-good-tile");
    expect(latest().status).toBe("error");
    map.success("a");
    expect(latest().status).toBe("error");
    map.emit("sourcedata", map.event({ tile: { state: "errored", tileID: { key: "b" } }, isSourceLoaded: true }));
    map.emit("sourcedata", map.event({ sourceDataType: "idle", isSourceLoaded: true }));
    expect(latest().status).toBe("error");
    map.success("b");
    expect(latest().status).toBe("loaded");
  });

  it("replaces the Level6 product/source with Level7, preserving display and insertion order", () => {
    const { map, controller, latest } = setup(primary, true, 0.31);
    const originalSource = map.getSource(SEA_ICE_SOURCE_ID);
    const route = map.getLayer("route");
    const oldErrorListener = [...map.listeners.get("error")!][0];
    const oldDataListener = [...map.listeners.get("sourcedata")!][0];
    map.success();
    expect(latest().selection).toBe(primary);
    controller.update({ selection: fallback, visible: false, opacity: 0.31 });
    expect(map.getSource(SEA_ICE_SOURCE_ID)).not.toBe(originalSource);
    expect(map.getSource(SEA_ICE_SOURCE_ID)).toMatchObject({ maxzoom: 7, attribution: fallback.attribution });
    expect(map.getSource(SEA_ICE_SOURCE_ID)?.tiles).toEqual([getSeaIceTileUrl(fallback.date, fallback)]);
    expect(map.removed).toEqual([SEA_ICE_LAYER_ID, SEA_ICE_SOURCE_ID]);
    expect(map.getLayer(SEA_ICE_LAYER_ID)).toMatchObject({ paint: { "raster-opacity": 0.31 }, layout: { visibility: "none" } });
    expect(map.layers.map((layer) => layer.id)).toEqual(["background", GEBCO_LAYER_ID, SEA_ICE_LAYER_ID, "route"]);
    expect(map.getLayer("route")).toBe(route);
    expect(map.listeners.get("error")?.size).toBe(1);
    expect(map.listeners.get("sourcedata")?.size).toBe(1);
    oldErrorListener(map.event({ error: new Error("late old error") }));
    oldDataListener(map.event({ tile: { state: "loaded", texture: {} }, isSourceLoaded: true }));
    map.emit("error", map.event({ source: originalSource, error: new Error("old URL") }));
    expect(latest()).toMatchObject({ status: "hidden", selection: fallback });
    controller.update({ selection: fallback, visible: true, opacity: 0.31 });
    expect(latest().status).toBe("loading");
    map.success();
    expect(latest()).toMatchObject({ status: "loaded", selection: fallback });
  });

  it("restarts real loading for a new date even when the product is unchanged", () => {
    const { map, controller, latest } = setup();
    map.success();
    const historical = { ...fallback, date: "2026-06-01", requestedDate: "2026-06-01" };
    controller.update({ selection: historical, visible: true, opacity: 0.7 });
    expect(latest()).toMatchObject({ status: "loading", selection: historical });
    expect(map.addedSources).toHaveLength(2);
    expect(map.getSource(SEA_ICE_SOURCE_ID)?.tiles[0]).toContain("2026-06-01/GoogleMapsCompatible_Level7");
    map.success();
    expect(latest().status).toBe("loaded");
  });

  it("updates opacity without replacing data and never reports a hidden empty source as loaded", () => {
    const { map, controller, latest } = setup(fallback, false);
    expect(latest().status).toBe("hidden");
    map.sourceLoaded = true;
    map.emit("sourcedata", map.event({ sourceDataType: "visibility", isSourceLoaded: true }));
    vi.advanceTimersByTime(30000);
    expect(latest().status).toBe("hidden");
    controller.update({ selection: fallback, visible: true, opacity: 0.65 });
    expect(latest().status).toBe("loading");
    map.success();
    controller.update({ selection: fallback, visible: true, opacity: 0.2 });
    expect(latest().status).toBe("loaded");
    expect(map.addedSources).toHaveLength(1);
    expect(map.getLayer(SEA_ICE_LAYER_ID)?.paint?.["raster-opacity"]).toBe(0.2);
    controller.update({ selection: fallback, visible: false, opacity: 0.2 });
    expect(latest().status).toBe("hidden");
    map.emit("error", map.event({ error: new Error("hidden in-flight request failed") }));
    expect(latest().status).toBe("hidden");
    controller.update({ selection: fallback, visible: true, opacity: 0.2 });
    expect(latest().status).toBe("error");
    map.success();
    expect(latest().status).toBe("loaded");
  });

  it("restores the current selection and display after a style reload and leaves other layers alone", () => {
    const { map, controller, latest } = setup(fallback, false, 0.4);
    const oldDataListener = [...map.listeners.get("sourcedata")!][0];
    map.sources.clear();
    map.layers = [{ id: "background", type: "background" }, { id: "navigation-route", type: "line" }];
    map.emit("style.load");
    expect(map.addedSources).toHaveLength(2);
    expect(map.getSource(SEA_ICE_SOURCE_ID)).toEqual(getSeaIceSourceConfig(fallback.date, fallback));
    expect(map.layers.map((layer) => layer.id)).toEqual(["background", SEA_ICE_LAYER_ID, "navigation-route"]);
    expect(map.getLayer(SEA_ICE_LAYER_ID)).toMatchObject({ paint: { "raster-opacity": 0.4 }, layout: { visibility: "none" } });
    expect(map.listeners.get("sourcedata")?.size).toBe(1);
    expect(map.listeners.get("style.load")?.size).toBe(1);
    controller.update({ selection: fallback, visible: true, opacity: 0.4 });
    oldDataListener(map.event({ tile: { state: "loaded", texture: {} }, isSourceLoaded: true }));
    expect(latest().status).toBe("loading");
    map.success();
    expect(latest().status).toBe("loaded");
    controller.dispose();
    expect(map.getLayer("navigation-route")).toBeDefined();
    expect(map.getLayer(SEA_ICE_LAYER_ID)).toBeUndefined();
    expect(map.getSource(SEA_ICE_SOURCE_ID)).toBeUndefined();
    expect(map.listeners.get("sourcedata")?.size).toBe(0);
    expect(map.listeners.get("style.load")?.size).toBe(0);
    const states: SeaIceLayerState[] = [];
    const restored = createSeaIceLayerController(map, { selection: fallback, visible: true, opacity: 0.65 }, (state) => states.push(state));
    cleanups.push(restored.dispose);
    map.success();
    expect(states[states.length - 1]).toMatchObject({ status: "loaded", selection: fallback });
  });

  it("bounds tile loading, permits later recovery, and makes disposed timers/listeners harmless", () => {
    const { map, controller, states, latest } = setup();
    const oldErrorListener = [...map.listeners.get("error")!][0];
    const oldDataListener = [...map.listeners.get("sourcedata")!][0];
    vi.advanceTimersByTime(19000);
    map.emit("sourcedata", map.event({ sourceDataType: "metadata", isSourceLoaded: true }));
    vi.advanceTimersByTime(1000);
    expect(latest()).toMatchObject({ status: "error", message: expect.stringContaining("did not finish loading") });
    map.emit("sourcedata", map.event({ sourceDataType: "idle", isSourceLoaded: true }));
    expect(latest().status).toBe("error");
    map.success();
    expect(latest()).toMatchObject({ status: "loaded", message: undefined });
    controller.dispose();
    controller.dispose();
    const count = states.length;
    oldErrorListener(map.event({ error: new Error("late failure") }));
    oldDataListener(map.event({ tile: { state: "loaded", texture: {} }, isSourceLoaded: true }));
    map.emit("style.load");
    vi.advanceTimersByTime(30000);
    expect(states).toHaveLength(count);
    expect(vi.getTimerCount()).toBe(0);
  });

  it("keeps initialization failures unavailable until a style reload can restore imagery", () => {
    const map = new FakeMap();
    vi.spyOn(map, "addLayer").mockImplementationOnce(() => { throw new Error("style changed during creation"); });
    const states: SeaIceLayerState[] = [];
    const controller = createSeaIceLayerController(map, { selection: fallback, visible: true, opacity: 0.5 }, (state) => states.push(state));
    cleanups.push(controller.dispose);
    expect(states[states.length - 1]).toMatchObject({ status: "error", message: expect.stringContaining("initialized") });
    map.sourceLoaded = true;
    map.emit("sourcedata", map.event({ sourceDataType: "metadata", isSourceLoaded: true }));
    expect(states[states.length - 1].status).toBe("error");
    map.emit("style.load");
    expect(states[states.length - 1].status).toBe("loading");
    map.success();
    expect(states[states.length - 1].status).toBe("loaded");
  });

  it("keeps stale selection/date information separate from tile-network errors", () => {
    const { map, latest } = setup(primary);
    expect(latest().selection).toBe(primary);
    map.success();
    expect(latest()).toMatchObject({ status: "loaded", selection: { date: "2025-09-01", stale: true } });
    expect(getSeaIceSnapshotNote(latest().selection!, "latest")).toBe("Stale snapshot · latest available");
    map.failure("failed");
    expect(latest()).toMatchObject({ status: "error", selection: { date: "2025-09-01", stale: true } });
    expect(latest().message).toContain("tiles temporarily unavailable");
    expect(getSeaIceSnapshotNote({ ...primary, stale: false }, "custom")).toBe("Historical snapshot");
    expect(getSeaIceSnapshotNote({ ...primary, requestedDate: "2025-09-03" }, "custom")).toBe("Historical snapshot · stale snapshot · requested 2025-09-03");
  });
});

describe("single-owner sea-ice availability requests", () => {
  it("resolves once and propagates the exact actual selection, not a guessed date", async () => {
    const states: SeaIceAvailabilityState[] = [];
    const resolve = vi.fn().mockResolvedValue(fallback);
    cleanups.push(requestSeaIceAvailability("latest", undefined, (state) => states.push(state), resolve));
    expect(states).toEqual([{ selection: null, status: "loading", message: undefined }]);
    await vi.advanceTimersByTimeAsync(0);
    expect(resolve).toHaveBeenCalledTimes(1);
    expect(resolve).toHaveBeenCalledWith("latest", undefined);
    expect(states[states.length - 1]).toEqual({ selection: fallback, status: "ready" });
    expect(states[states.length - 1].selection).toBe(fallback);
    expect(vi.getTimerCount()).toBe(0);
  });

  it("ignores an outdated request result and cancels deferred work before it starts", async () => {
    let finish: (selection: SeaIceSelection) => void = () => {};
    const pending = new Promise<SeaIceSelection>((resolve) => { finish = resolve; });
    const oldStates: SeaIceAvailabilityState[] = [];
    const oldResolver = vi.fn().mockReturnValue(pending);
    const cancel = requestSeaIceAvailability("custom", primary.date, (state) => oldStates.push(state), oldResolver);
    await vi.advanceTimersByTimeAsync(0);
    cancel();
    const newStates: SeaIceAvailabilityState[] = [];
    cleanups.push(requestSeaIceAvailability("latest", undefined, (state) => newStates.push(state), vi.fn().mockResolvedValue(fallback)));
    finish(primary);
    await vi.advanceTimersByTimeAsync(0);
    expect(oldStates).toHaveLength(1);
    expect(newStates[newStates.length - 1].selection).toBe(fallback);
    const neverCalled = vi.fn().mockResolvedValue(primary);
    const cancelImmediately = requestSeaIceAvailability("latest", undefined, () => {}, neverCalled);
    cancelImmediately();
    await vi.advanceTimersByTimeAsync(0);
    expect(neverCalled).not.toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
  });

  it("retries metadata failure just once, then reports unavailable with no selected data", async () => {
    const states: SeaIceAvailabilityState[] = [];
    const resolve = vi.fn().mockRejectedValue(new Error("capabilities unavailable"));
    cleanups.push(requestSeaIceAvailability("latest", undefined, (state) => states.push(state), resolve));
    await vi.advanceTimersByTimeAsync(0);
    expect(states[states.length - 1].message).toContain("retrying once");
    await vi.advanceTimersByTimeAsync(1500);
    expect(resolve).toHaveBeenCalledTimes(2);
    expect(states[states.length - 1]).toMatchObject({ selection: null, status: "error", message: expect.stringContaining("capabilities unavailable") });
    await vi.advanceTimersByTimeAsync(60000);
    expect(resolve).toHaveBeenCalledTimes(2);
    expect(vi.getTimerCount()).toBe(0);
  });

  it("times out stuck metadata without overlapping retries or accepting a late result", async () => {
    let finish: (selection: SeaIceSelection) => void = () => {};
    const pending = new Promise<SeaIceSelection>((resolve) => { finish = resolve; });
    const states: SeaIceAvailabilityState[] = [];
    const resolve = vi.fn().mockReturnValue(pending);
    cleanups.push(requestSeaIceAvailability("latest", undefined, (state) => states.push(state), resolve));
    await vi.advanceTimersByTimeAsync(12000);
    expect(states[states.length - 1]).toMatchObject({ selection: null, status: "error", message: expect.stringContaining("timed out") });
    finish(fallback);
    await vi.advanceTimersByTimeAsync(30000);
    expect(resolve).toHaveBeenCalledTimes(1);
    expect(states[states.length - 1].status).toBe("error");
  });
});
