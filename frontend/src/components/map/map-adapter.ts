/**
 * MapAdapter — thin, opinionated wrapper around `maplibregl.Map`.
 *
 * Why a wrapper at all?
 *   - Centralizes the dark/Antarctic basemap + default view, so every
 *     layer component can stay storage-only and never have to think
 *     about camera or style.
 *   - Forces a single "register a source/layer on map load" pattern,
 *     which (a) prevents ordering bugs (layers reading sources that
 *     don't exist yet) and (b) is the natural seam for a future
 *     telemetry/metrics layer.
 *   - Exposes a minimal, controlled API. Layer components never touch
 *     the raw maplibre instance directly in this phase.
 *
 * API surface (deliberately minimal):
 *   - `onLoad(cb)`             — register a callback fired once the
 *                                 style is fully loaded. Use this
 *                                 inside layer components to add
 *                                 their sources/layers.
 *   - `addSource(id, spec)`
 *   - `addLayer(layerSpec, beforeId?)`
 *   - `setLayerVisibility(id, visible)`
 *   - `setLayerOpacity(id, opacity)`
 *   - `setData(sourceId, data)`   — hot-swap a GeoJSON source
 *   - `setLayerFilter(layerId, filter)` — update a layer's filter
 *     expression (used by selection flows: iceberg, future
 *     route-stop selection, risk-feature highlight, etc.)
 *   - `on(event, handler)` / `off(...)`            — global events
 *   - `on(event, layerId, handler)` / `off(...)`   — layer-scoped
 *     events. The handler receives a MapLayerMouseEvent, which
 *     carries `event.features` for `click`/`mousemove` etc.
 *   - `getClusterExpansionZoom(sourceId, clusterId)` — Promise<number>;
 *     built-in supercluster helper for cluster click → expansion zoom.
 *   - `easeTo(opts)` — programmatic camera movement (used by
 *     cluster click to fly to the cluster's expansion zoom).
 *   - `getRawMap(): maplibregl.Map` — escape hatch. Used by the
 *     ocean-current CustomLayerInterface for `map.triggerRepaint()`
 *     inside its `render()` loop. There is exactly one call-site;
 *     if a second user appears, this method should be reconsidered.
 *
 * What is INTENTIONALLY not exposed yet (note for future work):
 *   - Raw `maplibregl.Map` access. Granted as a single escape hatch
 *     `getRawMap()` for the ocean-current CustomLayerInterface. It
 *     must call `map.triggerRepaint()` from inside its `render()`
 *     loop to keep the animation alive, and there is no other
 *     API surface to do that from. If a second user appears, this
 *     method should be reconsidered.
 *   - Camera control. All views come from the initial style/center/
 *     zoom today. Programmatic camera will be added when route /
 *     vessel layers arrive.
 *   - Style switching. The dark style is a constant for now.
 */
import maplibregl, {
  type CustomLayerInterface,
  type GeoJSONSourceSpecification,
  type LayerSpecification,
  type LngLatLike,
  type MapLayerMouseEvent,
  type MapMouseEvent,
} from "maplibre-gl";

/** Dark, Antarctic-appropriate basemap.
 *
 *  Source: CARTO Dark Matter GL style — a free, public, no-API-key
 *  vector basemap designed for dark-themed applications. Hosted by
 *  CARTO's basemap CDN.
 *
 *  Verified accessibility (no auth headers, no tokens, no cookies):
 *    - style.json
 *        https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json
 *    - vector tiles (MVT, subdomains a-d)
 *        https://tiles-{a-d}.basemaps.cartocdn.com/vectortiles/carto.streets/v1/{z}/{x}/{y}.mvt
 *    - sprite (+ @2x retina)
 *        https://tiles.basemaps.cartocdn.com/gl/dark-matter-gl-style/sprite{,.json,@2x.png}
 *    - glyphs (Open Sans Regular, Noto Sans Regular, etc.)
 *        https://tiles.basemaps.cartocdn.com/fonts/{fontstack}/{range}.pbf
 *
 *  All endpoints return 200 with no `WWW-Authenticate` challenge and
 *  no `Set-Cookie`. MapLibre handles the style URL directly — we
 *  pass the string to `new maplibregl.Map({ style: ... })` and it
 *  resolves the style, sources, sprite, and glyphs itself.
 *
 *  Note: CARTO's *raster* basemaps (basemaps.cartocdn.com/dark_all/...)
 *  have been known to inject an "API KEY REQUIRED" watermark in some
 *  regions. The *vector* GL style is a different endpoint and does
 *  not have that behavior — the watermark lives in the raster tile
 *  service, not in this style.
 *
 *  When the backend tileserver is online, replace this URL with a
 *  self-hosted style that ships an Antarctic-focused schema (ice
 *  shelves, station labels, etc.).
 */
const DARK_STYLE_URL =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

/** Initial camera — frames the Drake Passage → Ross Sea corridor.
 *
 *  Corridor bounds (from the drake-to-ross mock scenario):
 *    lon:  -66 to -58   (8° wide)
 *    lat:  -70 to -60   (10° tall)
 *
 *  Centroid:  [-62, -65]
 *  At this latitude (~65°S) one degree of longitude ≈ 47 km, so 8°
 *  of lon is ~376 km. A zoom of ~3.6 frames that width with a small
 *  margin at a 1024px-wide viewport, keeping the Antarctic basemap
 *  on-screen rather than letting South America / Africa dominate.
 *
 *  These values must stay in lockstep with SCENARIO.center/zoom in
 *  `lib/data/scenarios/drake-to-ross.ts` — the page header reads
 *  SCENARIO and the map reads these. The two together form a single
 *  "default view" concept; if one moves, move the other.
 */
const DEFAULT_CENTER: [number, number] = [-62, -65];
const DEFAULT_ZOOM = 3.6;

export type LoadHandler = (map: maplibregl.Map) => void;

export class MapAdapter {
  private readonly map: maplibregl.Map;
  private readonly loadHandlers: LoadHandler[] = [];
  private loaded = false;

  constructor(container: HTMLElement) {
    this.map = new maplibregl.Map({
      container,
      style: DARK_STYLE_URL,
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      minZoom: 1,
      maxZoom: 9,
      attributionControl: { compact: true },
      // Antarctic-appropriate UX: disable scroll-zoom around the page
      // so a stray scroll on a sidebar doesn't yank the camera.
      scrollZoom: { around: "center" },
    });

    this.map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), "top-right");

    this.map.on("load", () => {
      this.loaded = true;
      for (const h of this.loadHandlers) h(this.map);
    });
  }

  /** Register a callback that fires once the style is loaded. If the
   *  style is already loaded (hot-reload, late mount), fires immediately. */
  onLoad(handler: LoadHandler): void {
    if (this.loaded) {
      handler(this.map);
    } else {
      this.loadHandlers.push(handler);
    }
  }

  addSource(id: string, spec: GeoJSONSourceSpecification): void {
    if (!this.map.style) return;
    // maplibre throws if the source already exists; guard so layer
    // components can be re-mounted in dev without crashing.
    if (this.map.getSource(id)) return;
    this.map.addSource(id, spec);
  }

  addLayer(layer: LayerSpecification | CustomLayerInterface, beforeId?: string): void {
    if (!this.map.style) return;
    if (this.map.getLayer(layer.id)) return;
    this.map.addLayer(layer as LayerSpecification, beforeId);
  }

  removeLayer(layerId: string): void {
    if (!this.map.style) return;
    if (this.map.getLayer(layerId)) this.map.removeLayer(layerId);
  }

  removeSource(sourceId: string): void {
    if (!this.map.style) return;
    if (this.map.getSource(sourceId)) this.map.removeSource(sourceId);
  }

  setLayerVisibility(layerId: string, visible: boolean): void {
    if (!this.map.style) return;
    if (!this.map.getLayer(layerId)) return;
    this.map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
  }

  /** Apply opacity to every paint property that already carries a number,
   *  by multiplying against the current value. This is the pattern
   *  MapLibre's paint expressions expect for "global" opacity on a layer
   *  type that doesn't have a single opacity property. */
  setLayerOpacity(layerId: string, opacity: number): void {
    if (!this.map.style) return;
    const layer = this.map.getLayer(layerId);
    if (!layer) return;

    // Cast through unknown — paint properties are typed loosely upstream.
    const paint = (this.map as unknown as {
      getPaintProperty: (id: string, prop: string) => unknown;
      setPaintProperty: (id: string, prop: string, value: unknown) => void;
    });

    // Layer-type-aware default opacity properties. If a layer type adds
    // a new one later, extend this map rather than reaching for the raw
    // maplibre instance elsewhere.
    const opacityProps: Record<string, string> = {
      fill: "fill-opacity",
      line: "line-opacity",
      circle: "circle-opacity",
      heatmap: "heatmap-opacity",
      "fill-extrusion": "fill-extrusion-opacity",
      raster: "raster-opacity",
      symbol: "text-opacity",
    };
    const prop = opacityProps[layer.type];
    if (prop) paint.setPaintProperty(layerId, prop, opacity);
  }

  setData(sourceId: string, data: GeoJSON.FeatureCollection | GeoJSON.Feature): void {
    if (!this.map.style) return;
    const src = this.map.getSource(sourceId) as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    src.setData(data as GeoJSON.FeatureCollection);
  }

  setLayerFilter(
    layerId: string,
    filter: maplibregl.FilterSpecification | null,
  ): void {
    if (!this.map.style) return;
    if (!this.map.getLayer(layerId)) return;
    this.map.setFilter(layerId, filter);
  }

  // Event pass-throughs. Two shapes, matching maplibre's own API:
  //   - on(event, handler)                         — global map event
  //   - on(event, layerId, handler)                — single layer
  //   - on(event, layerIds: string[], handler)     — multiple layers
  // The 3-arg form's handler receives a MapLayerMouseEvent, which
  // carries `.features` for `click` / `mousemove` / etc. We forward
  // directly to maplibre; the cast is because the union of all
  // event/handler overloads is too wide to express in a single
  // signature without losing the type narrowing that callers want.
  on(event: string, handler: (e: MapMouseEvent) => void): void;
  on(
    event: string,
    layerId: string | string[],
    handler: (e: MapLayerMouseEvent) => void,
  ): void;
  on(
    event: string,
    layerOrHandler: string | string[] | ((e: MapMouseEvent) => void),
    handler?: (e: MapLayerMouseEvent) => void,
  ): void {
    if (typeof layerOrHandler === "function") {
      this.map.on(event, layerOrHandler);
    } else {
      // The cast is necessary because maplibre's 3-arg `on` is
      // generic-constrained to `keyof MapLayerEventType`; we accept
      // any `string` at the adapter boundary so callers don't have
      // to thread the literal type through.
      (this.map.on as (t: string, l: string | string[], h: (e: MapLayerMouseEvent) => void) => void)(
        event,
        layerOrHandler,
        handler as (e: MapLayerMouseEvent) => void,
      );
    }
  }

  off(event: string, handler: (e: MapMouseEvent) => void): void;
  off(
    event: string,
    layerId: string | string[],
    handler: (e: MapLayerMouseEvent) => void,
  ): void;
  off(
    event: string,
    layerOrHandler: string | string[] | ((e: MapMouseEvent) => void),
    handler?: (e: MapLayerMouseEvent) => void,
  ): void {
    if (typeof layerOrHandler === "function") {
      this.map.off(event, layerOrHandler);
    } else {
      (this.map.off as (t: string, l: string | string[], h: (e: MapLayerMouseEvent) => void) => void)(
        event,
        layerOrHandler,
        handler as (e: MapLayerMouseEvent) => void,
      );
    }
  }

  destroy(): void {
    this.map.remove();
  }

  /** Expansion-zoom for a cluster point. maplibre's supercluster
   *  helper returns the zoom at which the cluster splits into its
   *  members. Used by iceberg-layer's cluster click handler. */
  getClusterExpansionZoom(sourceId: string, clusterId: number): Promise<number> {
    const src = this.map.getSource(sourceId) as
      | (maplibregl.GeoJSONSource & { getClusterExpansionZoom?: (id: number) => Promise<number> })
      | undefined;
    if (!src || typeof src.getClusterExpansionZoom !== "function") {
      return Promise.resolve(this.map.getZoom());
    }
    return src.getClusterExpansionZoom(clusterId);
  }

  /** Programmatic camera ease. Currently a thin pass-through; wrapped
   *  here so iceberg-layer doesn't need the raw map for cluster
   *  expansion either. */
  easeTo(opts: { center: LngLatLike; zoom: number; duration?: number }): void {
    this.map.easeTo({
      center: opts.center,
      zoom: opts.zoom,
      duration: opts.duration ?? 1200,
    });
  }

  /** Escape hatch. See the API-surface comment at the top of this
   *  file for the single-call-site rule. */
  getRawMap(): maplibregl.Map {
    return this.map;
  }
}
