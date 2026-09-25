# SIH REHEARSAL TIMING
**Project:** SIH 26059

## Measured Timings
*Note: Browser UI automation was unverified in this CI environment; these timings represent backend API execution benchmarks.*

- **Backend Startup:** ~2 seconds (uvicorn/FastAPI).
- **Model Preflight Check:** < 1 second.
- **Route Calculation (API):** ~1.5 - 2.5 seconds (Dependent on A* distance grid scaling).
- **Safety Fallback Intercept (HTTP 400):** < 50ms (Immediate `RouteOrchestrator` block when data is missing).

## Rehearsal Schedule
- **Presentation Segment:** 5 minutes.
- **Live Demo Execution (Happy Path):** 2 minutes.
- **Live Demo Execution (Safety/Failure Demo):** 1 minute.
- **Judge Q&A Buffer:** 2 minutes.
