/**
 * NASA GIBS Sea Ice Concentration raster layer configuration for MapLibre GL JS.
 *
 * Products: AMSRU2_Sea_Ice_Concentration_12km (primary), GHRSST MUR (fallback)
 * Source:   NASA GIBS WMTS (REST tiles)
 * Endpoint: https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/
 * CRS:      EPSG:3857
 * Format:   image/png
 * Availability, matrix and zoom are resolved from WMTS capabilities.
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
 * Legacy date hint only; use resolveAvailableSeaIce for advertised availability.
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
export function getSeaIceTileUrl(
  date: string,
  selection?: SeaIceSelection,
): string {
  return (
    `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/` +
    `${selection?.productId ?? SEA_ICE_PRODUCT}/default/${date}/` +
    `${selection?.tileMatrixSet ?? "GoogleMapsCompatible_Level6"}/{z}/{y}/{x}.png`
  );
}

/**
 * MapLibre raster source configuration for sea-ice concentration.
 */
export function getSeaIceSourceConfig(date: string, selection?: SeaIceSelection) {
  return {
    type: "raster" as const,
    tiles: [getSeaIceTileUrl(date, selection)],
    tileSize: 256,
    maxzoom: selection?.maxZoom ?? 6,
    attribution: selection?.attribution ?? SEA_ICE_ATTRIBUTION,
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

export type SeaIceSelection = {
  productId: string;
  label: string;
  date: string;
  tileMatrixSet: string;
  maxZoom: number;
  attribution: string;
  stale: boolean;
  requestedDate?: string;
};

export type SeaIceResolverOptions = {
  now?: () => number;
  fetch?: typeof globalThis.fetch;
};

/** Legacy date-mode helper; does not check NASA's advertised availability. */
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

const CAPABILITIES_URL =
  "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml";
const DAY_MS = 86_400_000;
const CATALOG_TTL_MS = 60 * 60 * 1_000;
const REQUEST_TIMEOUT_MS = 10_000;
const MAX_XML_LENGTH = 16 * 1024 * 1024;
const WMTS_NS = "http://www.opengis.net/wmts/1.0";
const OWS_NS = "http://www.opengis.net/ows/1.1";

const PRODUCTS = [
  {
    productId: SEA_ICE_PRODUCT,
    label: "AMSR-U2 Sea Ice Concentration 12km",
    attribution: SEA_ICE_ATTRIBUTION,
  },
  {
    productId: "GHRSST_L4_MUR_Sea_Ice_Concentration",
    label: "GHRSST L4 MUR Sea Ice Concentration",
    attribution: "NASA GIBS — GHRSST L4 MUR Sea Ice Concentration",
  },
] as const;

type DateRange = { start: number; end: number };
type CatalogLayer = {
  productId: string;
  label: string;
  attribution: string;
  tileMatrixSet: string;
  maxZoom: number;
  defaultDate?: number;
  ranges: DateRange[];
};
type RawDimension = {
  identifiers: string[];
  defaults: string[];
  values: string[];
};
type RawLayer = {
  identifiers: string[];
  dimensions: RawDimension[];
  matrices: string[];
};
type XmlKind =
  | "capabilities"
  | "contents"
  | "layer"
  | "dimension"
  | "link"
  | "layerIdentifier"
  | "dimensionIdentifier"
  | "default"
  | "value"
  | "matrix";
type XmlFrame = {
  qName: string;
  namespaces: Record<string, string>;
  kind?: XmlKind;
  text?: string;
  layer?: RawLayer;
  dimension?: RawDimension;
};

function malformedMetadata(): never {
  throw new Error("NASA GIBS capabilities metadata is malformed or unsupported.");
}

/** Deliberately no DTD/custom entity support: metadata never needs it. */
function decodeXmlText(text: string): string {
  return text.replace(
    /&(?:#x([\da-fA-F]+)|#(\d+)|(amp|lt|gt|quot|apos));|&/g,
    (
      _match,
      hex: string | undefined,
      decimal: string | undefined,
      name: string | undefined,
    ) => {
      if (name) {
        return { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'" }[name]!;
      }
      const code = hex ? parseInt(hex, 16) : decimal ? Number(decimal) : NaN;
      if (
        code === 9 ||
        code === 10 ||
        code === 13 ||
        (code >= 0x20 && code <= 0xd7ff) ||
        (code >= 0xe000 && code <= 0xfffd) ||
        (code >= 0x10000 && code <= 0x10ffff)
      ) {
        return String.fromCodePoint(code);
      }
      return malformedMetadata();
    },
  );
}

/**
 * Bounded, namespace-aware XML extraction, usable in browsers and Node tests.
 * Only direct WMTS Layer/Dimension/TileMatrixSetLink children are retained;
 * style identifiers, matrix definitions and unrelated products cannot leak in.
 */
function extractLayers(xml: string): RawLayer[] {
  if (
    !xml ||
    xml.length > MAX_XML_LENGTH ||
    /[\u0000-\u0008\u000B\u000C\u000E-\u001F]/.test(xml)
  ) {
    return malformedMetadata();
  }
  const layers: RawLayer[] = [];
  const stack: XmlFrame[] = [];
  let rootSeen = false;
  let unnamespaced = false;
  let elements = 0;
  let cursor = 0;

  function appendText(text: string, cdata = false) {
    const frame = stack[stack.length - 1];
    if (!frame) {
      if (cdata || text.trim()) malformedMetadata();
      return;
    }
    const decoded = cdata ? text : decodeXmlText(text);
    if (frame.text !== undefined) frame.text += decoded;
  }

  function closeFrame(qName: string) {
    const frame = stack.pop();
    if (!frame || frame.qName !== qName) malformedMetadata();
    const text = frame.text?.trim() ?? "";
    switch (frame.kind) {
      case "layerIdentifier":
        frame.layer!.identifiers.push(text);
        break;
      case "dimensionIdentifier":
        frame.dimension!.identifiers.push(text);
        break;
      case "default":
        frame.dimension!.defaults.push(text);
        break;
      case "value":
        frame.dimension!.values.push(text);
        break;
      case "matrix":
        frame.layer!.matrices.push(text);
        break;
    }
  }

  while (cursor < xml.length) {
    const start = xml.indexOf("<", cursor);
    if (start < 0) {
      appendText(xml.slice(cursor));
      cursor = xml.length;
      break;
    }
    appendText(xml.slice(cursor, start));
    if (
      xml.startsWith("<!--", start) ||
      xml.startsWith("<?", start) ||
      xml.startsWith("<![CDATA[", start)
    ) {
      const comment = xml.startsWith("<!--", start);
      const cdata = xml.startsWith("<![CDATA[", start);
      const prefixLength = comment ? 4 : cdata ? 9 : 2;
      const terminator = comment ? "-->" : cdata ? "]]>" : "?>";
      const end = xml.indexOf(terminator, start + prefixLength);
      if (end < 0) malformedMetadata();
      const text = xml.slice(start + prefixLength, end);
      if (comment && text.includes("--")) malformedMetadata();
      if (cdata) appendText(text, true);
      cursor = end + terminator.length;
      continue;
    }
    // Scan the tag boundary respecting quoted attributes, including xmlns.
    let end = start + 1;
    let quote = "";
    for (; end < xml.length; end++) {
      const char = xml[end];
      if (quote) {
        if (char === quote) quote = "";
      } else if (char === '"' || char === "'") {
        quote = char;
      } else if (char === ">") {
        break;
      } else if (char === "<") {
        malformedMetadata();
      }
    }
    if (end === xml.length || end - start > 65_536) malformedMetadata();
    let tag = xml.slice(start + 1, end);
    cursor = end + 1;
    if (tag.startsWith("/")) {
      const closing = /^\/([A-Za-z_][\w.-]*(?::[A-Za-z_][\w.-]*)?)\s*$/.exec(tag);
      if (!closing) malformedMetadata();
      closeFrame(closing[1]);
      continue;
    }
    const selfClosing = /\/\s*$/.test(tag);
    if (selfClosing) tag = tag.replace(/\/\s*$/, "");
    const name = /^([A-Za-z_][\w.-]*(?::[A-Za-z_][\w.-]*)?)/.exec(tag);
    if (!name || ++elements > 250_000 || stack.length >= 64) malformedMetadata();
    const parent = stack[stack.length - 1];
    if (parent?.text !== undefined) malformedMetadata();
    const namespaces: Record<string, string> = {
      ...(parent?.namespaces ?? { xml: "http://www.w3.org/XML/1998/namespace" }),
    };
    const attributes = new Set<string>();
    const attribute =
      /\s+([A-Za-z_][\w.-]*(?::[A-Za-z_][\w.-]*)?)\s*=\s*(?:"([^"<]*)"|'([^'<]*)')/g;
    let position = name[0].length;
    while (tag.slice(position).trim()) {
      attribute.lastIndex = position;
      const match = attribute.exec(tag);
      if (
        !match ||
        match.index !== position ||
        attributes.has(match[1]) ||
        attributes.size >= 128
      ) {
        malformedMetadata();
      }
      attributes.add(match[1]);
      const value = decodeXmlText(match[2] ?? match[3]);
      if (match[1] === "xmlns") namespaces[""] = value;
      else if (match[1].startsWith("xmlns:")) namespaces[match[1].slice(6)] = value;
      position = attribute.lastIndex;
    }
    const qName = name[1];
    const parts = qName.split(":");
    const prefix = parts.length === 2 ? parts[0] : "";
    const localName = parts[parts.length - 1];
    if (prefix && !Object.prototype.hasOwnProperty.call(namespaces, prefix)) {
      malformedMetadata();
    }
    const namespace = namespaces[prefix] ?? "";
    if (!parent) {
      if (
        rootSeen ||
        localName !== "Capabilities" ||
        (namespace && namespace !== WMTS_NS)
      ) {
        malformedMetadata();
      }
      rootSeen = true;
      unnamespaced = namespace === "";
    }
    const wmts = namespace === WMTS_NS || (unnamespaced && namespace === "");
    const ows = namespace === OWS_NS || (unnamespaced && namespace === "");
    const frame: XmlFrame = {
      qName,
      namespaces,
      layer: parent?.layer,
      dimension: parent?.dimension,
    };
    if (!parent) frame.kind = "capabilities";
    else if (parent.kind === "capabilities" && wmts && localName === "Contents") {
      frame.kind = "contents";
    } else if (parent.kind === "contents" && wmts && localName === "Layer") {
      frame.kind = "layer";
      frame.layer = { identifiers: [], dimensions: [], matrices: [] };
      layers.push(frame.layer);
    } else if (parent.kind === "layer" && ows && localName === "Identifier") {
      frame.kind = "layerIdentifier";
    } else if (parent.kind === "layer" && wmts && localName === "Dimension") {
      frame.kind = "dimension";
      frame.dimension = { identifiers: [], defaults: [], values: [] };
      frame.layer!.dimensions.push(frame.dimension);
    } else if (parent.kind === "dimension" && ows && localName === "Identifier") {
      frame.kind = "dimensionIdentifier";
    } else if (parent.kind === "dimension" && wmts && localName === "Default") {
      frame.kind = "default";
    } else if (parent.kind === "dimension" && wmts && localName === "Value") {
      frame.kind = "value";
    } else if (parent.kind === "layer" && wmts && localName === "TileMatrixSetLink") {
      frame.kind = "link";
    } else if (parent.kind === "link" && wmts && localName === "TileMatrixSet") {
      frame.kind = "matrix";
    }
    if (
      frame.kind &&
      ["layerIdentifier", "dimensionIdentifier", "default", "value", "matrix"].includes(frame.kind)
    ) {
      frame.text = "";
    }
    stack.push(frame);
    if (selfClosing) closeFrame(qName);
  }
  if (!rootSeen || stack.length) malformedMetadata();
  return layers;
}

function parseUtcDate(value: string): number | undefined {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return undefined;
  const timestamp = Date.parse(`${value}T00:00:00.000Z`);
  if (
    !Number.isFinite(timestamp) ||
    new Date(timestamp).toISOString().slice(0, 10) !== value
  ) {
    return undefined;
  }
  return timestamp;
}

function parseRange(value: string): DateRange | undefined {
  const parts = value.trim().split("/");
  if (parts.length !== 1 && (parts.length !== 3 || parts[2] !== "P1D")) {
    return undefined;
  }
  const start = parseUtcDate(parts[0]);
  const end = parseUtcDate(parts.length === 1 ? parts[0] : parts[1]);
  if (start === undefined || end === undefined || start > end) return undefined;
  return { start, end };
}

function coversDate(layer: CatalogLayer, date: number): boolean {
  return layer.ranges.some((range) => date >= range.start && date <= range.end);
}

function parseCatalog(xml: string): CatalogLayer[] {
  const rawLayers = extractLayers(xml);
  const catalog: CatalogLayer[] = [];
  for (const product of PRODUCTS) {
    const matchingLayers = rawLayers.filter(
      (layer) =>
        layer.identifiers.length === 1 &&
        layer.identifiers[0] === product.productId,
    );
    // Ambiguous or incomplete product metadata cannot establish availability.
    if (matchingLayers.length !== 1) continue;
    const raw = matchingLayers[0];
    const time = raw.dimensions.filter(
      (dimension) =>
        dimension.identifiers.length === 1 && dimension.identifiers[0] === "Time",
    );
    if (
      time.length !== 1 ||
      !time[0].values.length ||
      time[0].defaults.length > 1
    ) {
      continue;
    }
    const defaultDate = time[0].defaults.length
      ? parseUtcDate(time[0].defaults[0])
      : undefined;
    if (time[0].defaults.length && defaultDate === undefined) continue;
    const ranges = time[0].values
      .flatMap((value) => value.split(","))
      .map(parseRange);
    if (!ranges.length || ranges.some((range) => !range)) continue;
    const matrices = raw.matrices
      .flatMap((tileMatrixSet) => {
        const match = /^GoogleMapsCompatible_Level([0-9]|1[0-9]|2[0-4])$/.exec(
          tileMatrixSet,
        );
        return match ? [{ tileMatrixSet, maxZoom: Number(match[1]) }] : [];
      })
      .sort((a, b) => b.maxZoom - a.maxZoom);
    if (!matrices.length) continue;
    catalog.push({
      ...product,
      ...matrices[0],
      defaultDate,
      ranges: ranges as DateRange[],
    });
  }
  if (!catalog.length) {
    throw new Error(
      "NASA GIBS capabilities advertise no usable sea-ice layers with date coverage and a supported tile matrix.",
    );
  }
  return catalog;
}

type CatalogCache = {
  catalog?: CatalogLayer[];
  fetchedAt: number;
  expiresAt: number;
  inFlight?: Promise<CatalogLayer[]>;
};
// Keying by fetch also isolates callers that provide a different data source in tests.
const catalogCaches = new WeakMap<typeof globalThis.fetch, CatalogCache>();

async function fetchCatalog(
  fetcher: typeof globalThis.fetch,
): Promise<CatalogLayer[]> {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_resolve, reject) => {
    timer = setTimeout(() => {
      reject(
        new Error("NASA GIBS availability request timed out after 10 seconds."),
      );
      controller.abort();
    }, REQUEST_TIMEOUT_MS);
  });
  try {
    const request = async () => {
      const response = await fetcher(CAPABILITIES_URL, {
        signal: controller.signal,
        headers: { Accept: "application/xml" },
      });
      if (!response.ok) {
        throw new Error(
          `NASA GIBS availability request failed (HTTP ${response.status}).`,
        );
      }
      if (Number(response.headers.get("content-length")) > MAX_XML_LENGTH) {
        malformedMetadata();
      }
      return parseCatalog(await response.text());
    };
    return await Promise.race([request(), timeout]);
  } catch (error) {
    controller.abort();
    if (error instanceof Error && error.message.startsWith("NASA GIBS")) {
      throw error;
    }
    throw new Error(
      `Unable to load NASA GIBS availability: ${error instanceof Error ? error.message : "request failed"}.`,
    );
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}

function loadCatalog(
  fetcher: typeof globalThis.fetch,
  now: () => number,
): Promise<CatalogLayer[]> {
  let cache = catalogCaches.get(fetcher);
  if (!cache) {
    cache = { fetchedAt: 0, expiresAt: 0 };
    catalogCaches.set(fetcher, cache);
  }
  const timestamp = now();
  if (
    cache.catalog &&
    timestamp >= cache.fetchedAt &&
    timestamp < cache.expiresAt
  ) {
    return Promise.resolve(cache.catalog);
  }
  if (cache.inFlight) return cache.inFlight;
  const entry = cache;
  entry.inFlight = fetchCatalog(fetcher)
    .then((catalog) => {
      entry.catalog = catalog;
      entry.fetchedAt = now();
      entry.expiresAt = entry.fetchedAt + CATALOG_TTL_MS;
      return catalog;
    })
    .catch((error: unknown) => {
      entry.catalog = undefined;
      entry.expiresAt = 0;
      throw error;
    })
    .finally(() => {
      entry.inFlight = undefined;
    });
  return entry.inFlight;
}

function latestCoveredDate(
  layer: CatalogLayer,
  today: number,
): number | undefined {
  let latest =
    layer.defaultDate !== undefined &&
    layer.defaultDate <= today &&
    coversDate(layer, layer.defaultDate)
      ? layer.defaultDate
      : undefined;
  for (const range of layer.ranges) {
    const date = Math.min(range.end, today);
    if (date >= range.start && (latest === undefined || date > latest)) {
      latest = date;
    }
  }
  return latest;
}

/**
 * Resolve only advertised snapshots. Latest favors a primary <=3 UTC days old,
 * then a fresh fallback, then the freshest older product. Explicit dates never
 * substitute a different day; missing/invalid metadata is an actionable error.
 */
export async function resolveAvailableSeaIce(
  mode: SeaIceDateMode,
  customDate?: string,
  options: SeaIceResolverOptions = {},
): Promise<SeaIceSelection> {
  const now = options.now ?? Date.now;
  const timestamp = now();
  if (!Number.isFinite(timestamp)) {
    throw new Error("Invalid sea-ice resolver clock.");
  }
  const today = Math.floor(timestamp / DAY_MS) * DAY_MS;
  let requestedDate: string | undefined;
  let requestedTimestamp: number | undefined;
  if (mode === "yesterday") {
    requestedTimestamp = today - DAY_MS;
    requestedDate = new Date(requestedTimestamp).toISOString().slice(0, 10);
  } else if (mode === "custom") {
    requestedDate = customDate;
    requestedTimestamp =
      customDate === undefined ? undefined : parseUtcDate(customDate);
    if (requestedTimestamp === undefined) {
      throw new Error("A valid sea-ice date in YYYY-MM-DD format is required.");
    }
    if (requestedTimestamp > today) {
      throw new Error("Sea-ice dates cannot be in the future (UTC).");
    }
  } else if (mode !== "latest") {
    throw new Error("Unknown sea-ice date mode.");
  }
  const catalog = await loadCatalog(options.fetch ?? globalThis.fetch, now);
  let chosen: { layer: CatalogLayer; date: number } | undefined;
  if (requestedTimestamp !== undefined) {
    const layer = catalog.find((candidate) =>
      coversDate(candidate, requestedTimestamp),
    );
    if (layer) chosen = { layer, date: requestedTimestamp };
    else {
      throw new Error(
        `NASA GIBS does not advertise sea-ice coverage for requested UTC date ${requestedDate}.`,
      );
    }
  } else {
    const candidates = catalog.flatMap((layer) => {
      const date = latestCoveredDate(layer, today);
      return date === undefined ? [] : [{ layer, date }];
    });
    // Catalog order is primary, fallback; sorting preserves primary for ties.
    chosen =
      candidates.find((candidate) => today - candidate.date <= 3 * DAY_MS) ??
      candidates.sort((a, b) => b.date - a.date)[0];
    if (!chosen) {
      throw new Error(
        "NASA GIBS advertises no sea-ice snapshots on or before the current UTC date.",
      );
    }
  }
  const { layer, date } = chosen;
  return {
    productId: layer.productId,
    label: layer.label,
    date: new Date(date).toISOString().slice(0, 10),
    tileMatrixSet: layer.tileMatrixSet,
    maxZoom: layer.maxZoom,
    attribution: layer.attribution,
    stale: today - date > 3 * DAY_MS,
    ...(requestedDate ? { requestedDate } : {}),
  };
}
