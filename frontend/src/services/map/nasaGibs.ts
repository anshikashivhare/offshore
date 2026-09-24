/**
 * NASA GIBS Sea Ice Concentration raster layer configuration for MapLibre GL JS.
 *
 * Product:  AMSRU2_Sea_Ice_Concentration_12km
 * Source:   NASA GIBS WMTS (REST tiles)
 * Endpoint: https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/
 * CRS:      EPSG:3857
 * Format:   image/png
 * MaxZoom:  6  (GoogleMapsCompatible_Level6)
 */

export const SEA_ICE_SOURCE_ID = "sea-ice-gibs-source";
export const SEA_ICE_LAYER_ID = "sea-ice-gibs-layer";
export const SEA_ICE_PRODUCT = "AMSRU2_Sea_Ice_Concentration_12km";

export const SEA_ICE_ATTRIBUTION =
  "NASA GIBS — AMSR-U2 Sea Ice Concentration 12km";

/** Default opacity for sea-ice overlay (0.0–1.0). */
export const SEA_ICE_DEFAULT_OPACITY = 0.55;

/**
 * Returns a YYYY-MM-DD string.
 * NASA GIBS ingests data with a ~1–2 day delay, so "latest available"
 * typically means 2 days ago.
 */
export function getLatestSeaIceDate(): string {
  const d = new Date(Date.now() - 2 * 86_400_000);
  return d.toISOString().split("T")[0];
}

export function getYesterdayDate(): string {
  const d = new Date(Date.now() - 86_400_000);
  return d.toISOString().split("T")[0];
}

/** Build the GIBS WMTS REST tile URL template for a given date. */
export function getSeaIceTileUrl(date: string): string {
  return (
    `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/` +
    `${SEA_ICE_PRODUCT}/default/${date}/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png`
  );
}

/**
 * MapLibre raster source configuration for sea-ice concentration.
 */
export function getSeaIceSourceConfig(date: string) {
  return {
    type: "raster" as const,
    tiles: [getSeaIceTileUrl(date)],
    tileSize: 256,
    maxzoom: 6,
    attribution: SEA_ICE_ATTRIBUTION,
  };
}

/**
 * MapLibre raster layer definition for sea-ice concentration.
 */
export function getSeaIceLayerConfig(opacity: number) {
  return {
    id: SEA_ICE_LAYER_ID,
    type: "raster" as const,
    source: SEA_ICE_SOURCE_ID,
    paint: {
      "raster-opacity": opacity,
    },
  };
}

/**
 * Sea-ice date mode options for the UI control.
 */
export type SeaIceDateMode = "latest" | "yesterday" | "custom";

/** Resolve a date-mode + optional custom date to an actual date string. */
export function resolveSeaIceDate(
  mode: SeaIceDateMode,
  customDate?: string,
): string {
  switch (mode) {
    case "latest":
      return getLatestSeaIceDate();
    case "yesterday":
      return getYesterdayDate();
    case "custom":
      return customDate ?? getLatestSeaIceDate();
  }
}
