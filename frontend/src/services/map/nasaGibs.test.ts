import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getLatestSeaIceDate,
  getSeaIceLayerConfig,
  getSeaIceSourceConfig,
  getSeaIceTileUrl,
  getYesterdayDate,
  resolveAvailableSeaIce,
  resolveSeaIceDate,
  SEA_ICE_ATTRIBUTION,
  SEA_ICE_LAYER_ID,
  SEA_ICE_PRODUCT,
  SEA_ICE_SOURCE_ID,
} from "./nasaGibs";

const FALLBACK = "GHRSST_L4_MUR_Sea_Ice_Concentration";
const NOW = Date.parse("2026-10-09T13:45:00Z");
const HOUR = 3_600_000;

type LayerFixture = {
  id: string;
  defaultDate?: string;
  values?: string[];
  matrix?: string;
  extra?: string;
};
type XmlStyle = "default" | "prefixed" | "bare";

/** Real WMTS element structure; tests parse XML, not a fabricated catalog. */
function capabilities(layers: LayerFixture[], style: XmlStyle = "default"): string {
  const w = style === "prefixed" ? "w:" : "";
  const o = style === "bare" ? "" : "o:";
  const namespaces = style === "bare" ? "" :
    `${style === "prefixed" ? "xmlns:w" : "xmlns"}="http://www.opengis.net/wmts/1.0" ` +
    'xmlns:o="http://www.opengis.net/ows/1.1"';
  return `<?xml version="1.0" encoding="UTF-8"?>
    <${w}Capabilities ${namespaces} version="1.0.0">
      <${w}Contents>
        ${layers.map((layer) => `
          <${w}Layer>
            <${o}Title>Sea ice &amp; daily coverage</${o}Title>
            <${o}Identifier>${layer.id}</${o}Identifier>
            <${w}Style isDefault="true"><${o}Identifier>default</${o}Identifier></${w}Style>
            <${w}Dimension>
              <${o}Identifier>Time</${o}Identifier>
              ${layer.defaultDate === undefined ? "" : `<${w}Default>${layer.defaultDate}</${w}Default>`}
              ${layer.values?.map((value) => `<${w}Value>${value}</${w}Value>`).join("") ?? ""}
            </${w}Dimension>
            <${w}TileMatrixSetLink><${w}TileMatrixSet>${layer.matrix ?? "GoogleMapsCompatible_Level6"}</${w}TileMatrixSet></${w}TileMatrixSetLink>
            ${layer.extra ?? ""}
          </${w}Layer>`).join("")}
        <${w}TileMatrixSet><${o}Identifier>GoogleMapsCompatible_Level24</${o}Identifier></${w}TileMatrixSet>
      </${w}Contents>
    </${w}Capabilities>`;
}

function primary(date = "2025-09-01"): LayerFixture {
  return { id: SEA_ICE_PRODUCT, defaultDate: date, values: [`2012-07-02/${date}/P1D`] };
}

function fallback(date = "2026-10-08"): LayerFixture {
  return {
    id: FALLBACK,
    defaultDate: date,
    values: ["2026-09-01/2026-09-05/P1D", `2026-10-01/${date}/P1D`],
    matrix: "GoogleMapsCompatible_Level7",
  };
}

function mockFetch(xml: string) {
  return vi.fn<typeof fetch>().mockImplementation(async () => new Response(xml));
}

function options(fetcher: typeof fetch, now = NOW) {
  return { fetch: fetcher, now: () => now };
}

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("advertised latest sea-ice selection", () => {
  it("uses the current MUR fallback when the AMSR-U2 primary ended in 2025", async () => {
    const fetcher = mockFetch(capabilities([primary(), fallback()]));
    const selection = await resolveAvailableSeaIce("latest", undefined, options(fetcher));
    expect(selection).toEqual({
      productId: FALLBACK,
      label: "GHRSST L4 MUR Sea Ice Concentration",
      date: "2026-10-08",
      tileMatrixSet: "GoogleMapsCompatible_Level7",
      maxZoom: 7,
      attribution: "NASA GIBS — GHRSST L4 MUR Sea Ice Concentration",
      stale: false,
    });
    expect(fetcher.mock.calls[0][0]).toBe(
      "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml",
    );
    expect(getSeaIceTileUrl(selection.date, selection)).toBe(
      `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${FALLBACK}/default/2026-10-08/GoogleMapsCompatible_Level7/{z}/{y}/{x}.png`,
    );
    expect(getSeaIceSourceConfig(selection.date, selection)).toEqual({
      type: "raster",
      tiles: [getSeaIceTileUrl(selection.date, selection)],
      tileSize: 256,
      maxzoom: 7,
      attribution: selection.attribution,
    });
  });

  it("preserves the primary at the inclusive three-UTC-day freshness boundary", async () => {
    const fetcher = mockFetch(capabilities([fallback(), primary("2026-10-06")]));
    const selection = await resolveAvailableSeaIce("latest", undefined, options(fetcher));
    expect(selection).toMatchObject({ productId: SEA_ICE_PRODUCT, date: "2026-10-06", stale: false });
  });

  it("prefers a fresh fallback once the primary is over three UTC days old", async () => {
    const fetcher = mockFetch(capabilities([primary("2026-10-05"), fallback()]));
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({
      productId: FALLBACK, date: "2026-10-08", stale: false,
    });
  });

  it.each([
    ["2026-10-03", "2026-10-05", FALLBACK, "2026-10-05"],
    ["2026-10-05", "2026-10-03", SEA_ICE_PRODUCT, "2026-10-05"],
    ["2026-10-05", "2026-10-05", SEA_ICE_PRODUCT, "2026-10-05"],
  ])("marks the freshest older snapshot stale (primary %s, fallback %s)", async (p, f, productId, date) => {
    const fetcher = mockFetch(capabilities([primary(p), fallback(f)]));
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({
      productId, date, stale: true,
    });
  });

  it("caps ranges and a future default at today's UTC date", async () => {
    const fetcher = mockFetch(capabilities([primary("2026-10-20")]));
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({
      date: "2026-10-09", stale: false,
    });
  });

  it("does not select a future range or fill the gap before it", async () => {
    const layer = fallback("2026-10-20");
    layer.values = ["2026-10-01/2026-10-07/P1D", "2026-10-12/2026-10-20/P1D"];
    const fetcher = mockFetch(capabilities([layer]));
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({ date: "2026-10-07" });
  });

  it("fails if every advertised snapshot is in the future", async () => {
    const fetcher = mockFetch(capabilities([{ ...fallback("2026-10-20"), values: ["2026-10-12/2026-10-20/P1D"] }]));
    await expect(resolveAvailableSeaIce("latest", undefined, options(fetcher))).rejects.toThrow(/on or before the current UTC date/);
  });

  it("uses coverage rather than an older or out-of-range default", async () => {
    const fetcher = mockFetch(capabilities([{ ...primary("2026-10-08"), defaultDate: "2025-01-01" }]));
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({ date: "2026-10-08" });
  });
});

describe("exact yesterday and custom UTC dates", () => {
  it("resolves yesterday exactly through the fallback when only it supports that day", async () => {
    const fetcher = mockFetch(capabilities([primary(), fallback()]));
    expect(await resolveAvailableSeaIce("yesterday", undefined, options(fetcher))).toMatchObject({
      productId: FALLBACK, date: "2026-10-08", requestedDate: "2026-10-08", stale: false,
    });
  });

  it("uses yesterday in UTC even when a local offset crosses the day boundary", async () => {
    const fetcher = mockFetch(capabilities([primary("2026-10-09"), fallback()]));
    const now = Date.parse("2026-10-09T23:30:00-05:00");
    expect(await resolveAvailableSeaIce("yesterday", undefined, options(fetcher, now))).toMatchObject({
      productId: SEA_ICE_PRODUCT, date: "2026-10-09", requestedDate: "2026-10-09",
    });
  });

  it("prefers the primary for historical/custom dates covered by both products", async () => {
    const fetcher = mockFetch(capabilities([primary(), {
      ...fallback(), values: ["2025-01-01/2026-10-08/P1D"],
    }]));
    expect(await resolveAvailableSeaIce("custom", "2025-09-01", options(fetcher))).toMatchObject({
      productId: SEA_ICE_PRODUCT, date: "2025-09-01", requestedDate: "2025-09-01", stale: true,
    });
  });

  it.each(["2012-07-02", "2025-09-01"])("includes primary range endpoint %s", async (date) => {
    const fetcher = mockFetch(capabilities([primary()]));
    expect(await resolveAvailableSeaIce("custom", date, options(fetcher))).toMatchObject({ productId: SEA_ICE_PRODUCT, date });
  });

  it.each(["2026-10-01", "2026-10-03", "2026-10-06", "2026-10-08"])("includes separated fallback range endpoint %s", async (date) => {
    const fetcher = mockFetch(capabilities([primary(), {
      ...fallback(), values: ["2026-10-01/2026-10-03/P1D", "2026-10-06/2026-10-08/P1D"],
    }]));
    expect(await resolveAvailableSeaIce("custom", date, options(fetcher))).toMatchObject({ productId: FALLBACK, date });
  });

  it.each(["2026-10-04", "2026-10-05"])("rejects requested date %s in a range gap without substituting a nearby day", async (date) => {
    const fetcher = mockFetch(capabilities([primary(), {
      ...fallback(), values: ["2026-10-01/2026-10-03/P1D", "2026-10-06/2026-10-08/P1D"],
    }]));
    await expect(resolveAvailableSeaIce("custom", date, options(fetcher))).rejects.toThrow(`requested UTC date ${date}`);
  });

  it("fails for unsupported yesterday instead of using today's available snapshot", async () => {
    const fetcher = mockFetch(capabilities([{ id: SEA_ICE_PRODUCT, values: ["2026-10-09"] }]));
    await expect(resolveAvailableSeaIce("yesterday", undefined, options(fetcher))).rejects.toThrow(/requested UTC date 2026-10-08/);
  });

  it.each([undefined, "", "2026-2-03", "2026-02-30", "2026-13-01", "2026-10-09T00:00:00Z", "not-a-date"])("rejects invalid custom date %s before fetching", async (date) => {
    const fetcher = mockFetch(capabilities([primary()]));
    await expect(resolveAvailableSeaIce("custom", date, options(fetcher))).rejects.toThrow(/valid sea-ice date/);
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("rejects future custom dates before fetching", async () => {
    const fetcher = mockFetch(capabilities([primary("2026-10-20")]));
    await expect(resolveAvailableSeaIce("custom", "2026-10-10", options(fetcher))).rejects.toThrow(/future \(UTC\)/);
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("accepts actual leap days and isolated/comma-separated advertised values", async () => {
    const fetcher = mockFetch(capabilities([{ id: SEA_ICE_PRODUCT, values: ["2024-02-29,2026-10-01/2026-10-03/P1D"] }]));
    expect(await resolveAvailableSeaIce("custom", "2024-02-29", options(fetcher))).toMatchObject({ date: "2024-02-29" });
    await expect(resolveAvailableSeaIce("custom", "2024-03-01", options(fetcher))).rejects.toThrow(/does not advertise/);
  });
});

describe("WMTS XML availability extraction", () => {
  it.each<XmlStyle>(["default", "prefixed", "bare"])("parses %s namespace structure without a DOM parser", async (style) => {
    const fetcher = mockFetch(capabilities([primary(), fallback()], style));
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({
      productId: FALLBACK, date: "2026-10-08", maxZoom: 7,
    });
  });

  it("resolves locally declared unprefixed OWS identifiers inside default WMTS elements", async () => {
    const xml = capabilities([primary(), fallback()])
      .replaceAll("<o:Identifier>", '<Identifier xmlns="http://www.opengis.net/ows/1.1">')
      .replaceAll("</o:Identifier>", "</Identifier>");
    const fetcher = mockFetch(xml);
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({
      productId: FALLBACK, date: "2026-10-08", maxZoom: 7,
    });
  });

  it("ignores unrelated products, nested style identifiers and unrelated matrices/dimensions", async () => {
    const noisy = {
      ...primary("2026-10-06"),
      extra: `<Style><o:Identifier>${FALLBACK}</o:Identifier><Default>2026-10-09</Default></Style>
        <Dimension><o:Identifier>Elevation</o:Identifier><Default>2026-10-09</Default><Value>2026-10-09</Value></Dimension>
        <x:Dimension xmlns:x="urn:unrelated"><o:Identifier>Time</o:Identifier><x:Value>2026-10-09</x:Value></x:Dimension>
        <x:TileMatrixSetLink xmlns:x="urn:unrelated"><x:TileMatrixSet>GoogleMapsCompatible_Level24</x:TileMatrixSet></x:TileMatrixSetLink>`,
    };
    const unknown = { id: "Unrelated_Sea_Ice_Layer", values: ["2026-10-09"], extra: `<Style><o:Identifier>${SEA_ICE_PRODUCT}</o:Identifier></Style>` };
    const fetcher = mockFetch(capabilities([unknown, noisy]));
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({
      productId: SEA_ICE_PRODUCT, date: "2026-10-06", tileMatrixSet: "GoogleMapsCompatible_Level6", maxZoom: 6,
    });
  });

  it("decodes numeric/predefined XML entities and CDATA in direct metadata values", async () => {
    const xml = capabilities([primary("2026-10-08")])
      .replace(SEA_ICE_PRODUCT, "AMSRU2_Sea_Ice_Concentration_12k&#109;")
      .replace("<Default>2026-10-08</Default>", "<Default><![CDATA[2026-10-08]]></Default>")
      .replace("<TileMatrixSet>GoogleMapsCompatible_Level6", "<TileMatrixSet>GoogleMapsCompatible_Level&#54;");
    const fetcher = mockFetch(xml);
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({ productId: SEA_ICE_PRODUCT, date: "2026-10-08", maxZoom: 6 });
  });

  it("uses the advertised compatible matrix rather than assuming a product's usual level", async () => {
    const fetcher = mockFetch(capabilities([{ ...primary("2026-10-08"), matrix: "GoogleMapsCompatible_Level7" }]));
    const selection = await resolveAvailableSeaIce("latest", undefined, options(fetcher));
    expect(selection).toMatchObject({ productId: SEA_ICE_PRODUCT, maxZoom: 7, tileMatrixSet: "GoogleMapsCompatible_Level7" });
    expect(getSeaIceSourceConfig(selection.date, selection).maxzoom).toBe(7);
  });

  it("skips an unusable primary and resolves a correctly described fallback", async () => {
    const fetcher = mockFetch(capabilities([{ ...primary("2026-10-09"), values: undefined }, fallback()]));
    expect(await resolveAvailableSeaIce("latest", undefined, options(fetcher))).toMatchObject({ productId: FALLBACK });
  });

  it.each([
    { id: SEA_ICE_PRODUCT, defaultDate: "2026-10-08" },
    { id: SEA_ICE_PRODUCT, values: ["2026-02-30/2026-10-08/P1D"] },
    { id: SEA_ICE_PRODUCT, values: ["2026-10-08/2026-10-01/P1D"] },
    { id: SEA_ICE_PRODUCT, values: ["2026-10-01/2026-10-08/P2D"] },
    { id: SEA_ICE_PRODUCT, values: ["2026-10-08"], matrix: "EPSG4326_250m" },
    { id: SEA_ICE_PRODUCT, values: ["2026-10-08"], defaultDate: "bad-default" },
    { id: "Unrelated_Product", values: ["2026-10-08"] },
  ])("fails clearly for unusable advertised metadata: %j", async (layer) => {
    const fetcher = mockFetch(capabilities([layer]));
    await expect(resolveAvailableSeaIce("latest", undefined, options(fetcher))).rejects.toThrow(/no usable sea-ice layers/);
  });

  it.each([
    "not XML",
    "<Capabilities><Contents><Layer></Contents></Capabilities>",
    '<!DOCTYPE Capabilities [<!ENTITY injected "anything">]><Capabilities/>',
    '<Capabilities xmlns="urn:unrelated"><Contents/></Capabilities>',
    '<Capabilities><Contents></Contents>',
    '<Capabilities><Contents bad="&unknown;"/></Capabilities>',
    '<Capabilities><Contents a="1" a="2"/></Capabilities>',
  ])("rejects malformed or unsupported XML rather than guessing a current date", async (xml) => {
    const fetcher = mockFetch(xml);
    await expect(resolveAvailableSeaIce("latest", undefined, options(fetcher))).rejects.toThrow(/metadata is malformed/);
  });

  it("does not use a whitelisted product identifier from the wrong namespace", async () => {
    const xml = capabilities([primary("2026-10-08")])
      .replace(`xmlns:o="http://www.opengis.net/ows/1.1"`, `xmlns:o="urn:unrelated"`);
    const fetcher = mockFetch(xml);
    await expect(resolveAvailableSeaIce("latest", undefined, options(fetcher))).rejects.toThrow(/no usable sea-ice layers/);
  });

  it("rejects excessive XML nesting even outside the whitelisted fields", async () => {
    const xml = capabilities([fallback()]).replace(
      "</Contents>",
      `${"<Wrapper>".repeat(65)}${"</Wrapper>".repeat(65)}</Contents>`,
    );
    await expect(resolveAvailableSeaIce("latest", undefined, options(mockFetch(xml)))).rejects.toThrow(/metadata is malformed/);
  });

  it("rejects an oversized advertised body before reading it", async () => {
    const response = new Response(capabilities([fallback()]), {
      headers: { "content-length": String(16 * 1024 * 1024 + 1) },
    });
    const body = vi.spyOn(response, "text");
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response);
    await expect(resolveAvailableSeaIce("latest", undefined, options(fetcher))).rejects.toThrow(/metadata is malformed/);
    expect(body).not.toHaveBeenCalled();
    expect(fetcher.mock.calls[0][1]?.signal?.aborted).toBe(true);
  });
});

describe("availability request cache and recovery", () => {
  it("supports the public two-argument contract with the ambient clock and fetch", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
    const fetcher = mockFetch(capabilities([primary(), fallback()]));
    vi.stubGlobal("fetch", fetcher);
    expect(await resolveAvailableSeaIce("latest")).toMatchObject({ productId: FALLBACK, date: "2026-10-08" });
    expect(await resolveAvailableSeaIce("custom", "2025-09-01")).toMatchObject({ productId: SEA_ICE_PRODUCT, date: "2025-09-01" });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("caches for one hour and refreshes when the catalog expires", async () => {
    let now = NOW;
    const fetcher = mockFetch(capabilities([primary(), fallback()]));
    const injected = { fetch: fetcher, now: () => now };
    await resolveAvailableSeaIce("latest", undefined, injected);
    now += HOUR - 1;
    await resolveAvailableSeaIce("yesterday", undefined, injected);
    expect(fetcher).toHaveBeenCalledTimes(1);
    now += 1;
    await resolveAvailableSeaIce("latest", undefined, injected);
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("deduplicates concurrent requests across date modes", async () => {
    let complete!: (response: Response) => void;
    const pending = new Promise<Response>((resolve) => { complete = resolve; });
    const fetcher = vi.fn<typeof fetch>().mockReturnValue(pending);
    const injected = options(fetcher);
    const latest = resolveAvailableSeaIce("latest", undefined, injected);
    const yesterday = resolveAvailableSeaIce("yesterday", undefined, injected);
    const historical = resolveAvailableSeaIce("custom", "2025-09-01", injected);
    expect(fetcher).toHaveBeenCalledTimes(1);
    complete(new Response(capabilities([primary(), fallback()])));
    const selections = await Promise.all([latest, yesterday, historical]);
    expect(selections.map((selection) => selection.date)).toEqual(["2026-10-08", "2026-10-08", "2025-09-01"]);
    await resolveAvailableSeaIce("latest", undefined, injected);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it.each(["HTTP", "network", "XML", "coverage"])("retries after %s failures instead of caching a guessed date", async (kind) => {
    const fetcher = mockFetch(capabilities([primary(), fallback()]));
    if (kind === "HTTP") fetcher.mockResolvedValueOnce(new Response("unavailable", { status: 503 }));
    else if (kind === "network") fetcher.mockRejectedValueOnce(new Error("offline"));
    else if (kind === "XML") fetcher.mockResolvedValueOnce(new Response("<Capabilities>"));
    else fetcher.mockResolvedValueOnce(new Response(capabilities([{ id: SEA_ICE_PRODUCT, defaultDate: "2026-10-08" }])));
    const injected = options(fetcher);
    const first = resolveAvailableSeaIce("latest", undefined, injected);
    const concurrent = resolveAvailableSeaIce("yesterday", undefined, injected);
    const results = await Promise.allSettled([first, concurrent]);
    expect(results.every((result) => result.status === "rejected")).toBe(true);
    expect(fetcher).toHaveBeenCalledTimes(1);
    const failure = results[0];
    if (failure.status === "rejected") {
      expect(String(failure.reason)).toMatch(kind === "HTTP" ? /HTTP 503/ : kind === "network" ? /offline/ : kind === "XML" ? /malformed/ : /no usable/);
    }
    expect(await resolveAvailableSeaIce("latest", undefined, injected)).toMatchObject({ productId: FALLBACK, date: "2026-10-08" });
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("does not return an expired cached catalog after a refresh fails", async () => {
    let now = NOW;
    const fetcher = mockFetch(capabilities([primary(), fallback()]));
    const injected = { fetch: fetcher, now: () => now };
    await resolveAvailableSeaIce("latest", undefined, injected);
    now += HOUR;
    fetcher.mockResolvedValueOnce(new Response("down", { status: 502 }));
    await expect(resolveAvailableSeaIce("latest", undefined, injected)).rejects.toThrow(/HTTP 502/);
    expect(await resolveAvailableSeaIce("latest", undefined, injected)).toMatchObject({ date: "2026-10-08" });
    expect(fetcher).toHaveBeenCalledTimes(3);
  });

  it.each(["fetch", "body"])("times out a hung %s and recovers on the next request", async (stage) => {
    vi.useFakeTimers();
    const fetcher = mockFetch(capabilities([fallback()]));
    if (stage === "fetch") fetcher.mockImplementationOnce(() => new Promise<Response>(() => {}));
    else {
      const response = new Response("");
      vi.spyOn(response, "text").mockImplementation(() => new Promise<string>(() => {}));
      fetcher.mockResolvedValueOnce(response);
    }
    const injected = options(fetcher);
    const rejected = expect(resolveAvailableSeaIce("latest", undefined, injected)).rejects.toThrow(/timed out/);
    await vi.advanceTimersByTimeAsync(10_000);
    await rejected;
    expect(fetcher.mock.calls[0][1]?.signal?.aborted).toBe(true);
    expect(await resolveAvailableSeaIce("latest", undefined, injected)).toMatchObject({ date: "2026-10-08" });
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});

describe("legacy sea-ice helper compatibility", () => {
  it("preserves single-date tiles, source/layer IDs, layer opacity and legacy date helpers", () => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
    expect(getLatestSeaIceDate()).toBe("2026-10-07");
    expect(getYesterdayDate()).toBe("2026-10-08");
    expect(resolveSeaIceDate("latest")).toBe("2026-10-07");
    expect(resolveSeaIceDate("yesterday")).toBe("2026-10-08");
    expect(resolveSeaIceDate("custom", "2025-09-01")).toBe("2025-09-01");
    expect(getSeaIceTileUrl("2025-09-01")).toContain(`${SEA_ICE_PRODUCT}/default/2025-09-01/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png`);
    expect(getSeaIceSourceConfig("2025-09-01")).toMatchObject({ maxzoom: 6, attribution: SEA_ICE_ATTRIBUTION });
    expect(getSeaIceLayerConfig(0.4)).toEqual({
      id: SEA_ICE_LAYER_ID,
      type: "raster",
      source: SEA_ICE_SOURCE_ID,
      paint: { "raster-opacity": 0.4 },
    });
  });
});
