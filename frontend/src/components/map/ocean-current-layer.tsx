"use client";

/**
 * OceanCurrentLayer
 * -----------------
 * MapLibre CustomLayerInterface that renders a particle system advected
 * by the mock surface-current vector field. Conventions match
 * sea-ice-layer.tsx / iceberg-layer.tsx (exported SOURCE, adapter
 * load-registration, useLayerStore for enabled/opacity).
 *
 * Why a CustomLayerInterface, not a circle/line layer?
 *   - maplibre's standard layer types are declarative — they can't
 *     animate position/age attributes per frame. The particle effect
 *     is intrinsically procedural.
 *   - A CustomLayerInterface gives us the WebGL context inside
 *     `onAdd`, control of our own shaders, and a `render(gl, matrix)`
 *     callback fired every frame by maplibre's render loop.
 *
 * Performance budget:
 *   - Default 4000 particles, ~60 fps on integrated GPUs.
 *   - CPU per frame: 4000 bilinear lookups + 4000 position adds +
 *     4000 age increments ≈ <0.5ms.
 *   - GPU per frame: 4000 POINTS draws, two small attribute buffers.
 *
 * What is NOT a `requestAnimationFrame` loop in this file:
 *   - The animation is driven by maplibre's `render` callback, not a
 *     separate `requestAnimationFrame` (rAF). We *do* call
 *     `map.triggerRepaint()` once per frame from inside `render` so
 *     the map keeps redrawing while the layer is visible. When the
 *     layer is disabled, we set a flag that stops calling
 *     `triggerRepaint` and the render loop naturally idles.
 *
 * Color ramp (brand-aligned, see RAMP_CSS_GRADIENT below):
 *   - 5 stops: glacial → signal → lagoon → alert → hazard.
 *   - Driven by the dataviz skill's "color follows entity" rule and
 *     the design-system brand palette. The 5 stops are sequential on
 *     the speed axis; the warm shift at the high end reads as the
 *     "approaching danger" maritime status convention.
 *
 * How state is pushed into the live layer:
 *   - The layer's `useEffect` creates the CustomLayerInterface ONCE
 *     and stores its imperative handle in a ref.
 *   - The four downstream effects (enabled, opacity, particleCount,
 *     speedMultiplier) read the ref and call handle methods —
 *     never recreate the layer. The map.gl object isn't used outside
 *     this file's `getRawMap()` call-site (the adapter's only
 *     escape-hatch consumer; see map-adapter.ts header).
 */

import { useEffect, useRef } from "react";
import type { CustomLayerInterface } from "maplibre-gl";
import { MapAdapter } from "@/components/map/map-adapter";
import { useLayerStore } from "@/stores/use-layer-store";
import {
  useOceanCurrentControls,
  OCEAN_CURRENT_LIMITS,
} from "@/stores/use-ocean-current-controls";
import {
  CURRENT_MAX_SPEED_MS,
  SPAWN_BOUNDS,
  sampleFlow,
} from "@/lib/data/scenarios/drake-to-ross-currents";

export const SOURCE = "ocean-current-source";
export const LAYER_FLOW = "ocean-current-flow";

interface Props {
  adapter: MapAdapter;
}

/* ------------------------------------------------------------------
 * Shaders
 * ------------------------------------------------------------------
 * Premultiplied alpha — maplibre's CustomLayerInterface sets
 * `gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)` and expects colors
 * to come in already multiplied by alpha. See maplibre-gl.d.ts
 * around line 5780 in the CustomLayerInterface doc.
 */
const VERT_SRC = /* glsl */ `
attribute vec2 aPosition;   // lon, lat
attribute float aAge;       // 0..1, lifetime progress
attribute float aSpeed;     // normalized 0..1 against CURRENT_MAX_SPEED_MS

uniform float uPointSize;
uniform float uOpacity;
uniform mat4 uMatrix;       // maplibre's matrix (lon/lat → mercator → clip)

varying float vAge;
varying float vSpeed;

void main() {
  // Coordinate transform: aPosition is (lon, lat) in degrees. The
  // uMatrix uniform is maplibre's view-projection matrix, which
  // converts geographic coordinates (lon, lat) to clip-space
  // (-1..+1 in x/y) by way of mercator projection. This is the
  // ONLY transform needed — the result of the multiplication IS
  // the clip-space position, and gl_PointSize below is in screen
  // pixels (gl_PointSize is unaffected by the matrix).
  gl_Position = uMatrix * vec4(aPosition, 0.0, 1.0);

  // Constant point size for ALL particles — no speed-based jitter.
  // The previous version shrunk slow particles to ~70% of base
  // size, which produced hard-to-see "ghost" particles in the
  // calm regions of the field. The user spec is gl_PointSize >= 2.0;
  // we use a constant 8.0 (well above the floor) so every
  // particle reads clearly against the dark CARTO basemap.
  gl_PointSize = uPointSize;

  vAge = aAge;
  vSpeed = aSpeed;
}
`;

const FRAG_SRC = /* glsl */ `
precision mediump float;

varying float vAge;
varying float vSpeed;

uniform float uOpacity;

// 5-stop ramp. Index 0 = slowest (glacial), index 4 = fastest (hazard).
// Stops are POSITIONAL in the speed axis, not categorical hues, so
// they qualify as a sequential encoding (dataviz skill rule).
vec3 rampColor(float t) {
  vec3 c0 = vec3(0.498, 0.819, 0.827); // #7fd1d3 glacial
  vec3 c1 = vec3(0.369, 0.917, 0.831); // #5eead4 signal
  vec3 c2 = vec3(0.227, 0.663, 0.702); // #3aa9b3 lagoon
  vec3 c3 = vec3(0.984, 0.749, 0.141); // #fbbf24 alert
  vec3 c4 = vec3(0.973, 0.443, 0.443); // #f87171 hazard
  vec3 c;
  if (t < 0.25)        c = mix(c0, c1, t / 0.25);
  else if (t < 0.50)   c = mix(c1, c2, (t - 0.25) / 0.25);
  else if (t < 0.75)   c = mix(c2, c3, (t - 0.50) / 0.25);
  else                 c = mix(c3, c4, (t - 0.75) / 0.25);
  return c;
}

void main() {
  // Soft round point from gl_PointCoord.
  vec2 d = gl_PointCoord - vec2(0.5);
  float r = length(d);
  if (r > 0.5) discard;

  // Soft radial falloff: 1.0 at center, 0.0 at edge. The smoothstep
  // gives a soft anti-aliased edge rather than a hard circle.
  float circle = smoothstep(0.5, 0.0, r);
  vec3 col = rampColor(vSpeed);

  // Soft fade in over the first 10% of life, full brightness in the
  // middle, fade out over the last 30%. Alpha is clamped to a
  // 0.75 floor (75% of uOpacity) so even a particle at the tail
  // end of its life is still very visible against the dark CARTO
  // basemap. The previous 0.55 floor was producing a "twinkling"
  // effect at the respawn boundary — raising it to 0.75 keeps the
  // flow visually continuous.
  float fadeIn  = smoothstep(0.0, 0.10, vAge);
  float fadeOut = 1.0 - smoothstep(0.70, 1.0, vAge);
  float life = mix(0.75, 1.0, fadeIn * fadeOut);

  // Premultiplied alpha output: r/g/b already scaled by alpha.
  // With uOpacity = 0.8 (layer default), the center of a fresh
  // particle renders at alpha 0.8 × 1.0 × 1.0 = 0.8, and the
  // tail of an old particle at alpha 0.8 × 0.75 = 0.6. Both
  // values are well above the visibility threshold against the
  // dark basemap.
  float a = circle * life * uOpacity;
  gl_FragColor = vec4(col * a, a);
}
`;

/* ------------------------------------------------------------------
 * Color ramp CSS gradient (for the legend swatch)
 * ------------------------------------------------------------------ */
const RAMP_CSS_GRADIENT =
  "linear-gradient(90deg, #7fd1d3 0%, #5eead4 25%, #3aa9b3 50%, #fbbf24 75%, #f87171 100%)";

/* ------------------------------------------------------------------
 * Imperative handle that React effects drive into the live layer
 * ------------------------------------------------------------------ */
interface LayerHandle {
  setEnabled: (b: boolean) => void;
  setOpacity: (n: number) => void;
  setParticleCount: (n: number) => void;
  setSpeedMultiplier: (m: number) => void;
}

/* ------------------------------------------------------------------
 * Component
 * ------------------------------------------------------------------ */
export function OceanCurrentLayer({ adapter }: Props) {
  const enabled = useLayerStore((s) => s.layers.oceanCurrents.enabled);
  const opacity = useLayerStore((s) => s.layers.oceanCurrents.opacity);
  const particleCount = useOceanCurrentControls((s) => s.particleCount);
  const speedMultiplier = useOceanCurrentControls((s) => s.speedMultiplier);

  const handleRef = useRef<LayerHandle | null>(null);

  // Create the CustomLayerInterface exactly once, on map load.
  useEffect(() => {
    let mounted = true;

    adapter.onLoad(() => {
      if (!mounted) return;
      const layer = createCustomLayer({ adapter });
      handleRef.current = layer._oceanCurrent;
      adapter.addLayer(layer, /* beforeId */ undefined);

      // First-load sync. The four state-effects below run on mount but
      // the handle doesn't exist until this callback fires, so the
      // first invocation of each is a no-op. Read the current store
      // values NOW and push them in, so the layer comes up in the
      // correct state even if the user toggled controls before the
      // map finished loading.
      const s = useLayerStore.getState();
      const c = useOceanCurrentControls.getState();
      handleRef.current.setEnabled(s.layers.oceanCurrents.enabled);
      handleRef.current.setOpacity(s.layers.oceanCurrents.opacity);
      handleRef.current.setParticleCount(c.particleCount);
      handleRef.current.setSpeedMultiplier(c.speedMultiplier);

      // Also flip maplibre's layer visibility immediately. The
      // `enabled` effect below will keep this in sync for future
      // toggles; this is just the first paint.
      adapter.setLayerVisibility(LAYER_FLOW, s.layers.oceanCurrents.enabled);
    });

    return () => {
      mounted = false;
      adapter.removeLayerSafe(LAYER_FLOW);
      handleRef.current = null;
    };
  }, [adapter]);

  // Push state changes into the live layer without recreating it.

  // Enabled toggle: hide the layer in maplibre's layer stack AND
  // tell the imperative handle to stop calling triggerRepaint (which
  // is what keeps the animation loop alive). Both are needed — the
  // maplibre visibility flag is the "right" way to hide a layer, but
  // the render() loop also needs the early-return guard so it stops
  // spending CPU on a layer the user can't see.
  useEffect(() => {
    handleRef.current?.setEnabled(enabled);
    adapter.setLayerVisibility(LAYER_FLOW, enabled);
  }, [adapter, enabled]);

  useEffect(() => {
    handleRef.current?.setOpacity(opacity);
  }, [opacity]);

  useEffect(() => {
    handleRef.current?.setParticleCount(particleCount);
  }, [particleCount]);

  useEffect(() => {
    handleRef.current?.setSpeedMultiplier(speedMultiplier);
  }, [speedMultiplier]);

  return (
    <OceanCurrentPanel
      enabled={enabled}
      onToggle={() => useLayerStore.getState().toggle("oceanCurrents")}
    />
  );
}

/* ------------------------------------------------------------------
 * Control panel
 * ------------------------------------------------------------------ */
function OceanCurrentPanel({
  enabled,
  onToggle,
}: {
  enabled: boolean;
  onToggle: () => void;
}) {
  const {
    particleCount,
    speedMultiplier,
    setParticleCount,
    setSpeedMultiplier,
  } = useOceanCurrentControls();

  return (
    <div
      className="panel absolute bottom-16 right-4 z-10 w-[260px] p-3 text-sm"
      role="region"
      aria-label="Ocean current controls"
      style={{ opacity: enabled ? 1 : 0.55 }}
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
          Ocean currents
        </span>
        <Toggle checked={enabled} onChange={onToggle} />
      </div>

      {/* Mock-data notice. The particles are driven by a hand-authored
          1° control grid (see drake-to-ross-currents.ts), not by a
          live HYCOM/OSCAR feed. The label is intentionally muted
          (--fg-muted, not --status-warn) so it reads as a metadata
          note rather than an alert — the panel is still functional,
          just not authoritative. Tracking matches the panel header
          for visual consistency. */}
      <div
        className="mb-2 flex items-center gap-1.5 text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]"
        aria-label="Data source notice"
      >
        <span
          aria-hidden
          className="inline-block h-1.5 w-1.5 rounded-full"
          style={{ background: "var(--fg-muted)" }}
        />
        Mock data — placeholder
      </div>

      <SliderRow
        label="Particles"
        value={particleCount}
        min={OCEAN_CURRENT_LIMITS.particleMin}
        max={OCEAN_CURRENT_LIMITS.particleMax}
        step={100}
        format={(v) => v.toLocaleString()}
        onChange={setParticleCount}
        disabled={!enabled}
      />

      <SliderRow
        label="Speed"
        value={speedMultiplier}
        min={OCEAN_CURRENT_LIMITS.speedMin}
        max={OCEAN_CURRENT_LIMITS.speedMax}
        step={0.05}
        format={(v) => `${v.toFixed(2)}×`}
        onChange={setSpeedMultiplier}
        disabled={!enabled}
      />

      <div className="mt-3" aria-label="Speed legend">
        <div
          className="h-1.5 w-full rounded-sm border border-[color:var(--border-subtle)]"
          style={{ background: RAMP_CSS_GRADIENT }}
        />
        <div className="mt-1 flex items-center justify-between text-[10px] text-[color:var(--fg-muted)]">
          <span className="font-mono">0.00</span>
          <span className="font-mono">{(CURRENT_MAX_SPEED_MS * 0.5).toFixed(2)}</span>
          <span className="font-mono">{CURRENT_MAX_SPEED_MS.toFixed(2)}</span>
          <span className="uppercase tracking-[0.16em] text-[color:var(--fg-secondary)]">m/s</span>
        </div>
      </div>
    </div>
  );
}

function SliderRow({
  label,
  value,
  min,
  max,
  step,
  format,
  onChange,
  disabled,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  format: (v: number) => string;
  onChange: (v: number) => void;
  disabled: boolean;
}) {
  return (
    <div className="mt-1.5 flex items-center gap-2">
      <span className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)] w-14 shrink-0">
        {label}
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.currentTarget.value))}
        className="flex-1 accent-[color:var(--accent)] disabled:cursor-not-allowed"
        style={{ height: 4 }}
        aria-label={label}
      />
      <span
        className="text-right font-mono text-[11px] text-[color:var(--fg-primary)]"
        style={{ minWidth: 56 }}
      >
        {format(value)}
      </span>
    </div>
  );
}

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className="relative h-4 w-7 rounded-full border border-[color:var(--border-subtle)] transition-colors"
      style={{ background: checked ? "var(--accent)" : "var(--color-fog)" }}
    >
      <span
        className="absolute top-[1px] h-2.5 w-2.5 rounded-full transition-all"
        style={{
          left: checked ? "calc(100% - 11px)" : "1px",
          background: "var(--fg-primary)",
        }}
      />
    </button>
  );
}

/* ------------------------------------------------------------------
 * Visualization constants
 * ------------------------------------------------------------------
 * The mock field is in m/s (real oceanographic units). Position
 * buffers, however, are in degrees (the format the matrix uniform
 * expects). To make particles visibly flow on a map at z3.6 we
 * need to convert m/s → deg/s AND apply a visualization multiplier
 * (a typical Antarctic surface current at 0.15 m/s is sub-pixel per
 * second on screen, so the visualization multiplier scales the
 * motion up to a perceptible rate).
 *
 *   1° latitude = 111,320 m  (constant)
 *   1° longitude = 111,320 × cos(latitude) m
 *
 * With VIS_FACTOR = 300,000, a 0.15 m/s eastward current near
 * -65°S becomes ≈ 0.95 deg/s eastward → ≈ 19 px/s on screen at z3.6.
 * That's slow enough to look like a current, fast enough to read.
 */
const M_PER_DEG_LAT = 111320;
const VIS_FACTOR = 300_000;

/** Advect one particle by the local flow (u, v in m/s) over `dt`
 *  seconds. Returns the new (lon, lat) in degrees. */
function advect(
  lon: number,
  lat: number,
  uMs: number,
  vMs: number,
  dt: number,
): { lon: number; lat: number } {
  const cosLat = Math.cos((lat * Math.PI) / 180);
  // m/s × VIS_FACTOR = visualization-m/s, then /m_per_deg → deg/s
  const uVisMs = uMs * VIS_FACTOR;
  const vVisMs = vMs * VIS_FACTOR;
  const mPerDegLon = M_PER_DEG_LAT * (Math.abs(cosLat) < 1e-6 ? 1e-6 : cosLat);
  const dLon = (uVisMs * dt) / mPerDegLon;
  const dLat = (vVisMs * dt) / M_PER_DEG_LAT;
  return { lon: lon + dLon, lat: lat + dLat };
}

/* ------------------------------------------------------------------
 * CustomLayerInterface factory
 * ------------------------------------------------------------------
 * Builds a MapLibre CustomLayerInterface. We use the gl context
 * passed in by maplibre's CustomLayerInterface contract (onAdd
 * and render both receive it) — that context is the same one the
 * basemap draws into, so we share shaders, blend state, and the
 * framebuffer with maplibre. Calling `getContext("webgl", ...)`
 * ourselves is unsafe: the canvas may already have a context, and
 * re-requesting with different attributes either returns the
 * existing context (ignoring our attributes) or null. Using the
 * gl argument from maplibre is the supported way and the only
 * way to get a context whose blend state matches what maplibre
 * is using for the rest of the layer stack.
 */
function createCustomLayer(opts: { adapter: MapAdapter }): CustomLayerInterface & {
  _oceanCurrent: LayerHandle;
} {
  const { adapter } = opts;

  // Per-frame state lives on the layer object, not in React.
  let positions: Float32Array;
  let ages: Float32Array;
  let lifespans: Float32Array;
  let speeds: Float32Array;
  let particleCount = 4000;
  let enabled = true;
  let opacity = 0.9;
  let speedMultiplier = 1.0;

  // GPU resources. We don't preallocate gl/program/buffer refs —
  // they come from maplibre's onAdd. Until then, render() no-ops.
  let program: WebGLProgram | null = null;
  let positionBuf: WebGLBuffer | null = null;
  let ageBuf: WebGLBuffer | null = null;
  let speedBuf: WebGLBuffer | null = null;
  let aPosition = -1;
  let aAge = -1;
  let aSpeed = -1;
  let uPointSize: WebGLUniformLocation | null = null;
  let uOpacity: WebGLUniformLocation | null = null;
  let uMatrix: WebGLUniformLocation | null = null;

  let lastT = 0;
  let mapRef: import("maplibre-gl").Map | null = null;

  function compileShader(
    glCtx: WebGLRenderingContext | WebGL2RenderingContext,
    type: number,
    src: string,
  ): WebGLShader {
    const shader = glCtx.createShader(type)!;
    glCtx.shaderSource(shader, src);
    glCtx.compileShader(shader);
    if (!glCtx.getShaderParameter(shader, glCtx.COMPILE_STATUS)) {
      const log = glCtx.getShaderInfoLog(shader) ?? "(no log)";
      glCtx.deleteShader(shader);
      throw new Error(`OceanCurrentLayer shader compile failed: ${log}`);
    }
    return shader;
  }

  function buildProgram(
    glCtx: WebGLRenderingContext | WebGL2RenderingContext,
  ): WebGLProgram {
    const vs = compileShader(glCtx, glCtx.VERTEX_SHADER, VERT_SRC);
    const fs = compileShader(glCtx, glCtx.FRAGMENT_SHADER, FRAG_SRC);
    const p = glCtx.createProgram()!;
    glCtx.attachShader(p, vs);
    glCtx.attachShader(p, fs);
    glCtx.linkProgram(p);
    if (!glCtx.getProgramParameter(p, glCtx.LINK_STATUS)) {
      const log = glCtx.getProgramInfoLog(p) ?? "(no log)";
      glCtx.deleteProgram(p);
      throw new Error(`OceanCurrentLayer program link failed: ${log}`);
    }
    return p;
  }

  function seedParticles() {
    positions = new Float32Array(particleCount * 2);
    ages = new Float32Array(particleCount);
    lifespans = new Float32Array(particleCount);
    speeds = new Float32Array(particleCount);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 2 + 0] = rand(SPAWN_BOUNDS.lonMin, SPAWN_BOUNDS.lonMax);
      positions[i * 2 + 1] = rand(SPAWN_BOUNDS.latMin, SPAWN_BOUNDS.latMax);
      // Stagger ages so respawns don't all happen at once.
      ages[i] = Math.random();
      lifespans[i] = rand(1.5, 3.0);
      const { speed } = sampleFlow(positions[i * 2], positions[i * 2 + 1]);
      speeds[i] = CURRENT_MAX_SPEED_MS > 0 ? speed / CURRENT_MAX_SPEED_MS : 0;
    }
  }

  const layer: CustomLayerInterface & { _oceanCurrent: LayerHandle } = {
    id: LAYER_FLOW,
    type: "custom",
    renderingMode: "2d",
    onAdd(map, glCtx) {
      // Use the gl context that maplibre hands us. This is the same
      // context the basemap draws into, so the blend function
      // (premultiplied alpha, gl.ONE / gl.ONE_MINUS_SRC_ALPHA) and
      // the framebuffer are already set up correctly for our
      // premultiplied-alpha shader output.
      mapRef = map;
      program = buildProgram(glCtx);
      aPosition = glCtx.getAttribLocation(program, "aPosition");
      aAge = glCtx.getAttribLocation(program, "aAge");
      aSpeed = glCtx.getAttribLocation(program, "aSpeed");
      uPointSize = glCtx.getUniformLocation(program, "uPointSize");
      uOpacity = glCtx.getUniformLocation(program, "uOpacity");
      uMatrix = glCtx.getUniformLocation(program, "uMatrix");
      positionBuf = glCtx.createBuffer();
      ageBuf = glCtx.createBuffer();
      speedBuf = glCtx.createBuffer();
      seedParticles();
    },
    render(glCtx, matrix) {
      // If the user has the layer toggled off, maplibre will not
      // call render() (it skips layers with visibility: none), so
      // we don't need an enabled-guard here — visibility is the
      // source of truth. But we still defensively bail if the GPU
      // resources aren't ready (cold mount race during HMR).
      if (!program || !mapRef) return;
      if (!enabled) return;
      if (!positionBuf || !ageBuf || !speedBuf) return;

      const now = performance.now();
      const dt = lastT === 0 ? 0.016 : Math.min(0.05, (now - lastT) / 1000);
      lastT = now;

      // Advect each particle by the local flow, with a unit
      // conversion from m/s → deg/s and a visualization multiplier
      // so the motion is perceptible on screen. (See advect() above
      // for the math.)
      for (let i = 0; i < particleCount; i++) {
        const ix = i * 2;
        const lon = positions[ix];
        const lat = positions[ix + 1];
        const { u, v, speed } = sampleFlow(lon, lat);
        const { lon: nl, lat: nla } = advect(
          lon,
          lat,
          u * speedMultiplier,
          v * speedMultiplier,
          dt,
        );
        positions[ix] = nl;
        positions[ix + 1] = nla;
        speeds[i] = CURRENT_MAX_SPEED_MS > 0 ? speed / CURRENT_MAX_SPEED_MS : 0;

        ages[i] += dt / lifespans[i];
        if (
          ages[i] >= 1 ||
          positions[ix] < SPAWN_BOUNDS.lonMin ||
          positions[ix] > SPAWN_BOUNDS.lonMax ||
          positions[ix + 1] < SPAWN_BOUNDS.latMin ||
          positions[ix + 1] > SPAWN_BOUNDS.latMax
        ) {
          positions[ix] = rand(SPAWN_BOUNDS.lonMin, SPAWN_BOUNDS.lonMax);
          positions[ix + 1] = rand(SPAWN_BOUNDS.latMin, SPAWN_BOUNDS.latMax);
          ages[i] = 0;
          lifespans[i] = rand(1.5, 3.0);
        }
      }

      glCtx.useProgram(program);
      // Point size 8.0 px — well above the 2.0 floor the user
      // spec'd. A constant size (no speed-based jitter) ensures
      // every particle is the same size, so the slowest currents
      // (low-velocity ACC body) are just as visible as the
      // fastest jets. 8px is large enough to read clearly at
      // z3.6 (each particle ~1.5 m on a 1024px-wide viewport) but
      // not so large that 4000 particles overlap into a wash.
      glCtx.uniform1f(uPointSize, 8.0);
      glCtx.uniform1f(uOpacity, opacity);
      glCtx.uniformMatrix4fv(uMatrix, false, matrix);

      glCtx.bindBuffer(glCtx.ARRAY_BUFFER, positionBuf);
      glCtx.bufferData(glCtx.ARRAY_BUFFER, positions, glCtx.DYNAMIC_DRAW);
      glCtx.enableVertexAttribArray(aPosition);
      glCtx.vertexAttribPointer(aPosition, 2, glCtx.FLOAT, false, 0, 0);

      glCtx.bindBuffer(glCtx.ARRAY_BUFFER, ageBuf);
      glCtx.bufferData(glCtx.ARRAY_BUFFER, ages, glCtx.DYNAMIC_DRAW);
      glCtx.enableVertexAttribArray(aAge);
      glCtx.vertexAttribPointer(aAge, 1, glCtx.FLOAT, false, 0, 0);

      glCtx.bindBuffer(glCtx.ARRAY_BUFFER, speedBuf);
      glCtx.bufferData(glCtx.ARRAY_BUFFER, speeds, glCtx.DYNAMIC_DRAW);
      glCtx.enableVertexAttribArray(aSpeed);
      glCtx.vertexAttribPointer(aSpeed, 1, glCtx.FLOAT, false, 0, 0);

      glCtx.drawArrays(glCtx.POINTS, 0, particleCount);

      // Keep the animation alive. Without this, maplibre only
      // repaints on user interaction (pan/zoom). We call it every
      // frame, so the loop is continuous while the layer is visible.
      mapRef.triggerRepaint();
    },
    _oceanCurrent: {
      setEnabled: (b) => { enabled = b; },
      setOpacity: (n) => { opacity = n; },
      setParticleCount: (n) => {
        if (n === particleCount) return;
        particleCount = n;
        if (positions) seedParticles();
      },
      setSpeedMultiplier: (m) => { speedMultiplier = m; },
    },
  };

  // `adapter` is captured in the closure for symmetry; if a future
  // revision needs to read adapter state from inside render, the
  // closure is already in scope. The current render only uses
  // mapRef / program / the buffers.
  void adapter;
  return layer;
}

function rand(min: number, max: number): number {
  return min + Math.random() * (max - min);
}
