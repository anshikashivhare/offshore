# Offshore — Frontend

Next.js 14 (App Router) + TypeScript + MapLibre GL + Tailwind + Zustand.

## Run

```bash
npm install
npm run dev
```

Then open <http://localhost:3000>.

## Layout

```
frontend/
├── src/
│   ├── app/                  # Next.js App Router
│   │   ├── layout.tsx
│   │   └── page.tsx          # Dashboard (mission map + status rail)
│   ├── components/
│   │   └── map/
│   │       ├── map-adapter.ts        # maplibregl.Map wrapper
│   │       ├── mission-map.tsx       # composer (owns adapter)
│   │       ├── sea-ice-layer.tsx     # SOURCE + LAYER_HEATMAP
│   │       ├── iceberg-layer.tsx     # SOURCE + LAYER_DETECTION(+SELECTED)
│   │       └── map-legend.tsx        # display-only legend
│   ├── stores/
│   │   ├── use-layer-store.ts        # per-LayerId enabled + opacity
│   │   └── use-iceberg-selection.ts  # selected iceberg id
│   ├── lib/
│   │   ├── types/
│   │   │   └── layer.ts              # LayerId union + LAYER_META
│   │   └── data/
│   │       └── scenarios/
│   │           └── drake-to-ross.ts  # MOCK sea-ice + iceberg features
│   └── styles/
│       ├── tokens.css                # CSS variables (source of truth)
│       └── globals.css
├── tailwind.config.ts
├── next.config.mjs
├── tsconfig.json
└── package.json
```

## Conventions

- Layer components are **plugins** to `MapAdapter`, not wrappers
  around the map. They render `null` and push state into the adapter.
- Every layer exports a `SOURCE` constant (source id) and
  `LAYER_*` constants (layer ids). These strings are the cross-file
  contract — never inline them.
- All maplibre interaction goes through the adapter. Do not
  `import "maplibre-gl"` from a layer component.
- Layer visibility/opacity live in `useLayerStore`; selection
  state (e.g. `useIcebergSelection`) lives in a feature-specific
  store.

See code comments in `map-adapter.ts` for the full "what's exposed /
what's deferred" contract.
