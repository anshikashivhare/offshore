import React, { useEffect, useMemo, useState } from "react";
import { useMap } from "./map-components";
import type { Coordinate, Iceberg } from "@/lib/offshore-types";
import { calculateDistanceNm } from "./NavigationMode";

export interface IcebergHoverInfo {
  iceberg: Iceberg;
  x: number;
  y: number;
  distanceNm?: number;
}

interface IcebergsMapLayerProps {
  icebergs: Iceberg[];
  visible?: boolean;
  selectedIcebergId?: string | null;
  vesselPosition?: Coordinate;
  onHoverIceberg: (info: IcebergHoverInfo | null) => void;
  onClickIceberg: (iceberg: Iceberg) => void;
}

export function IcebergsMapLayer({
  icebergs = [],
  visible = true,
  selectedIcebergId,
  vesselPosition,
  onHoverIceberg,
  onClickIceberg,
}: IcebergsMapLayerProps) {
  const { map, isLoaded } = useMap();

  const sourceId = "offshore-icebergs-source";
  const circleLayerId = "offshore-icebergs-circle";

  // Build GeoJSON FeatureCollection with memoization: exactly one Point feature per iceberg
  const geojson = useMemo(() => {
    return {
      type: "FeatureCollection" as const,
      features: icebergs
        .filter((iceberg) => iceberg && iceberg.position && !isNaN(iceberg.position.lat) && !isNaN(iceberg.position.lng))
        .map((iceberg) => ({
          type: "Feature" as const,
          id: iceberg.id,
          geometry: {
            type: "Point" as const,
            coordinates: [iceberg.position.lng, iceberg.position.lat],
          },
          properties: {
            id: iceberg.id,
            iceberg_id: iceberg.id,
            sizeKm: iceberg.sizeKm,
            risk: iceberg.risk || "hazard",
            drift: iceberg.drift || "",
            imageSrc: iceberg.imageSrc || "",
          },
        })),
    };
  }, [icebergs]);

  const [styleEpoch, setStyleEpoch] = useState(0);

  // Re-sync layer when map style changes (e.g. Map/Globe toggle or Navigation basemap switch)
  useEffect(() => {
    if (!map) return;
    const handleStyleLoad = () => {
      setStyleEpoch((v) => v + 1);
    };
    map.on("style.load", handleStyleLoad);
    return () => {
      map.off("style.load", handleStyleLoad);
    };
  }, [map]);

  // Setup / Update single GeoJSON source and circle layer
  useEffect(() => {
    if (!map || !isLoaded) return;

    // 1. Point Source
    const existingSource = map.getSource(sourceId) as any;
    if (!existingSource) {
      map.addSource(sourceId, {
        type: "geojson",
        data: geojson as any,
      });
    } else {
      existingSource.setData(geojson);
    }

    // 2. Single circle layer for isolated points (clean red appearance, no ghost trails)
    if (!map.getLayer(circleLayerId)) {
      map.addLayer({
        id: circleLayerId,
        type: "circle",
        source: sourceId,
        paint: {
          "circle-color": [
            "case",
            ["==", ["get", "iceberg_id"], selectedIcebergId || ""],
            "#dc2626",
            "#ef4444",
          ],
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            1, 4,
            4, 5.5,
            7, 7,
            12, 9,
          ],
          "circle-opacity": 0.95,
          "circle-stroke-width": [
            "case",
            ["==", ["get", "iceberg_id"], selectedIcebergId || ""],
            2.5,
            1.5,
          ],
          "circle-stroke-color": [
            "case",
            ["==", ["get", "iceberg_id"], selectedIcebergId || ""],
            "#fef08a",
            "#ffffff",
          ],
          "circle-stroke-opacity": 0.95,
        },
      });
    } else {
      map.setPaintProperty(circleLayerId, "circle-color", [
        "case",
        ["==", ["get", "iceberg_id"], selectedIcebergId || ""],
        "#dc2626",
        "#ef4444",
      ]);
      map.setPaintProperty(circleLayerId, "circle-stroke-width", [
        "case",
        ["==", ["get", "iceberg_id"], selectedIcebergId || ""],
        2.5,
        1.5,
      ]);
      map.setPaintProperty(circleLayerId, "circle-stroke-color", [
        "case",
        ["==", ["get", "iceberg_id"], selectedIcebergId || ""],
        "#fef08a",
        "#ffffff",
      ]);
    }

    // Control visibility
    const visibility = visible ? "visible" : "none";
    if (map.getLayer(circleLayerId)) {
      map.setLayoutProperty(circleLayerId, "visibility", visibility);
    }
  }, [map, isLoaded, geojson, visible, selectedIcebergId, styleEpoch]);

  // Event handlers: Hover (tooltip) & Click (selection / focus only, NO persistent modal)
  useEffect(() => {
    if (!map || !isLoaded || !visible) return;

    const handleMouseEnter = (e: any) => {
      map.getCanvas().style.cursor = "pointer";
      if (e.features && e.features.length > 0) {
        const feat = e.features[0];
        const icebergId = feat.properties?.iceberg_id || feat.properties?.id;
        const iceberg = icebergs.find((i) => i.id === icebergId);
        if (iceberg) {
          const distNm = vesselPosition
            ? calculateDistanceNm(vesselPosition, iceberg.position)
            : undefined;
          onHoverIceberg({
            iceberg,
            x: e.originalEvent?.clientX ?? e.point.x,
            y: e.originalEvent?.clientY ?? e.point.y,
            distanceNm: distNm,
          });
        }
      }
    };

    const handleMouseMove = (e: any) => {
      if (e.features && e.features.length > 0) {
        const feat = e.features[0];
        const icebergId = feat.properties?.iceberg_id || feat.properties?.id;
        const iceberg = icebergs.find((i) => i.id === icebergId);
        if (iceberg) {
          const distNm = vesselPosition
            ? calculateDistanceNm(vesselPosition, iceberg.position)
            : undefined;
          onHoverIceberg({
            iceberg,
            x: e.originalEvent?.clientX ?? e.point.x,
            y: e.originalEvent?.clientY ?? e.point.y,
            distanceNm: distNm,
          });
        }
      }
    };

    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
      onHoverIceberg(null);
    };

    const handleCanvasMouseOut = (e: MouseEvent) => {
      if (!e.relatedTarget) {
        handleMouseLeave();
      }
    };

    const handleMapMouseMove = (e: any) => {
      const features = map.queryRenderedFeatures(e.point, { layers: [circleLayerId] });
      if (!features || features.length === 0) {
        handleMouseLeave();
      }
    };

    const handleClick = (e: any) => {
      if (e.features && e.features.length > 0) {
        const feat = e.features[0];
        const icebergId = feat.properties?.iceberg_id || feat.properties?.id;
        const iceberg = icebergs.find((i) => i.id === icebergId);
        if (iceberg) {
          onClickIceberg(iceberg);
        }
      }
    };

    map.on("mouseenter", circleLayerId, handleMouseEnter);
    map.on("mousemove", circleLayerId, handleMouseMove);
    map.on("mouseleave", circleLayerId, handleMouseLeave);
    map.on("click", circleLayerId, handleClick);
    map.on("mousemove", handleMapMouseMove);
    map.on("movestart", handleMouseLeave);
    map.on("zoomstart", handleMouseLeave);
    map.on("rotatestart", handleMouseLeave);

    const canvas = map.getCanvas();
    canvas.addEventListener("mouseleave", handleMouseLeave);
    canvas.addEventListener("mouseout", handleCanvasMouseOut);

    return () => {
      map.off("mouseenter", circleLayerId, handleMouseEnter);
      map.off("mousemove", circleLayerId, handleMouseMove);
      map.off("mouseleave", circleLayerId, handleMouseLeave);
      map.off("click", circleLayerId, handleClick);
      map.off("mousemove", handleMapMouseMove);
      map.off("movestart", handleMouseLeave);
      map.off("zoomstart", handleMouseLeave);
      map.off("rotatestart", handleMouseLeave);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
      canvas.removeEventListener("mouseout", handleCanvasMouseOut);
      map.getCanvas().style.cursor = "";
    };
  }, [map, isLoaded, visible, icebergs, vesselPosition, onHoverIceberg, onClickIceberg]);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (!map) return;
      try {
        if (map.getLayer(circleLayerId)) map.removeLayer(circleLayerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      } catch (err) {
        // safely ignore on unmount
      }
    };
  }, [map]);

  return null;
}
