/**
 * GEBCO WMS raster layer configuration for MapLibre GL JS.
 *
 * Uses the official GEBCO Web Map Service:
 *   https://wms.gebco.net/mapserv?
 *
 * Layer: GEBCO_LATEST — shaded-relief bathymetry (GEBCO_2026 Grid)
 * CRS:   EPSG:3857 (Web Mercator, MapLibre-compatible)
 */

export const GEBCO_SOURCE_ID = "gebco-wms-source";
export const GEBCO_LAYER_ID = "gebco-wms-layer";

export const GEBCO_ATTRIBUTION =
  "GEBCO Compilation Group (2026) GEBCO 2026 Grid";

/**
 * MapLibre raster source definition for the GEBCO WMS.
 * Uses `{bbox-epsg-3857}` placeholder which MapLibre replaces with the
 * tile's bounding box in Web Mercator coordinates.
 */
export function getGebcoSourceConfig() {
  return {
    type: "raster" as const,
    tiles: [
      "https://wms.gebco.net/mapserv?" +
        "SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap" +
        "&LAYERS=GEBCO_LATEST" +
        "&SRS=EPSG:3857" +
        "&BBOX={bbox-epsg-3857}" +
        // Request a 512px tile and tell MapLibre that it is 512px below. This
        // covers four times the screen area per request compared with the old
        // 256px configuration, while retaining the same on-screen detail.
        // Fewer WMS round trips noticeably reduces gaps while the globe is
        // first settling and during short pans.
        "&WIDTH=512&HEIGHT=512" +
        "&FORMAT=image/png",
    ],
    tileSize: 512,
    attribution: GEBCO_ATTRIBUTION,
  };
}

/**
 * MapLibre raster layer definition for GEBCO.
 * Inserted as the lowest visual layer (just above the dark-ocean background).
 */
export function getGebcoLayerConfig() {
  return {
    id: GEBCO_LAYER_ID,
    type: "raster" as const,
    source: GEBCO_SOURCE_ID,
    paint: {
      "raster-opacity": 1.0,
    },
  };
}
