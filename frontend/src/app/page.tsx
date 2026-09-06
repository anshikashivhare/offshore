import { MissionMap } from "@/components/map/mission-map";
import { SCENARIO } from "@/lib/data/scenarios/drake-to-ross";

/**
 * Dashboard root page.
 *
 * Two-zone layout:
 *   - Left: thin status rail (wordmark + scenario)
 *   - Right: full-bleed MissionMap
 *
 * Future phases will add a layer-toggle panel (left) and a route
 * inspector (right). The rail is intentionally minimal so those
 * panels can slot in without redesigning the shell.
 */
export default function DashboardPage() {
  return (
    <div className="grid h-screen w-screen grid-cols-[280px_1fr] overflow-hidden bg-[color:var(--bg-app)]">
      {/* Status rail */}
      <aside className="flex flex-col border-r border-[color:var(--border-subtle)] bg-[color:var(--bg-surface)] p-5">
        <header className="flex items-baseline gap-2">
          <span className="wordmark text-lg">OFFSHORE</span>
          <span className="wordmark__accent text-[10px] uppercase tracking-[0.2em]">
            v0
          </span>
        </header>

        <div className="mt-8">
          <div className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
            Scenario
          </div>
          <h2 className="mt-1 text-base font-semibold text-[color:var(--fg-primary)]">
            {SCENARIO.name}
          </h2>
          <p className="mt-1 text-xs text-[color:var(--fg-secondary)]">
            {SCENARIO.description}
          </p>
        </div>

        <div className="mt-8">
          <div className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
            Status
          </div>
          <ul className="mt-2 space-y-1.5 text-xs text-[color:var(--fg-secondary)]">
            <li>
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--status-safe)] mr-2 align-middle" />
              Layers nominal
            </li>
            <li>
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--status-warn)] mr-2 align-middle" />
              Mock data — not operational
            </li>
          </ul>
        </div>

        <footer className="mt-auto text-[10px] text-[color:var(--fg-muted)]">
          MoES / NCPOR · SIH PS 26059
        </footer>
      </aside>

      {/* Map */}
      <main className="relative">
        <MissionMap />
      </main>
    </div>
  );
}
