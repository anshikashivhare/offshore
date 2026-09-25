# PHASE 37: ARCHITECTURE EVOLUTION PLAN
**Project:** SIH 26059
**State:** ACTIVE DEVELOPMENT (POST-RC1)

## RC1 Baseline
The RC1 state has been preserved as a rollback baseline via Git tag `SIH-26059-RC1`. All future development iterates toward RC2 without destructively overwriting the validated prototype.

## Architectural Debt & Refactoring Goals

### 1. Provider-Based Data Architecture (EXTEND)
**Goal:** Decouple data providers from routing algorithms.
**Implementation:** Introduce abstract interfaces (`VesselProvider`, `IcebergProvider`). Production configurations will inject PostGIS implementations, while DEMO instances will inject synthetic providers.

### 2. Multi-Resolution Ocean Routing (REFACTOR)
**Goal:** Improve A* spatial resolution for critical hazards.
**Implementation:** Transition from a uniform coastal grid to a coarse global-ocean graph that dynamically refines grid edges down to finer granularity near Antarctic corridors.

### 3. RouteValidator Independence (REFACTOR)
**Goal:** True mathematical independence.
**Implementation:** Remove the shared dependency on `evaluate_edge_risk`. The Validator must run an independent geometric intersection (e.g., PostGIS `ST_Distance`) to prove the A* output is physically safe.

## Core Development Priority
1. **P0: PostgreSQL/PostGIS-backed Real Runtime**
   - **Target:** Establish the actual production environment. Unblock the core execution path.
2. **P0: Provider Interfaces**
   - **Target:** Strip `if DEMO_MODE` logic out of the scientific forecasting/routing scripts.
3. **P1: Multi-Resolution Graph**
   - **Target:** Sub-grid anomaly detection for long edges.
4. **P1: Independent Validator**
   - **Target:** Dedicated spatial validation without shared execution paths.

## Current Target Status
**ARCHITECTURE STATUS:** UNFROZEN
**RC1 BASELINE:** PRESERVED (Tag: SIH-26059-RC1)
**CURRENT TARGET:** P0 PostgreSQL/PostGIS-backed Real Runtime (Note: Currently waiting on environment `sudo`/infrastructure resolution before code refactoring begins).
