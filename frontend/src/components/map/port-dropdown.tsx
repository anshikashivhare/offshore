"use client";

import { useState, useRef, useEffect } from "react";
import { usePortStore, Port } from "@/stores/use-port-store";
import { useRouteStore } from "@/stores/use-route-store";
import type { GeocodeResult } from "@/lib/hooks/use-reverse-geocode";

interface Props {
  label: string;
  type: "origin" | "destination";
  currentName: GeocodeResult;
  lat: number;
  lon: number;
}

export function PortDropdown({ label, type, currentName, lat, lon }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const searchPorts = usePortStore((s) => s.searchPorts);
  const setOrigin = useRouteStore((s) => s.setOrigin);
  const setDestination = useRouteStore((s) => s.setDestination);
  
  const pendingSelection = useRouteStore((s) => s.pendingSelection);
  const setPendingSelection = useRouteStore((s) => s.setPendingSelection);

  const containerRef = useRef<HTMLDivElement>(null);
  
  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const results = searchPorts(query);

  const handleSelect = (p: Port) => {
    if (type === "origin") setOrigin({ lat: p.lat, lon: p.lon });
    else setDestination({ lat: p.lat, lon: p.lon });
    
    setIsOpen(false);
    setQuery("");
  };

  const isPending = pendingSelection === type;

  return (
    <div className="relative w-full" ref={containerRef}>
      <button
        className="w-full text-left px-2 py-1 border rounded flex justify-between items-start transition-colors"
        style={{
          borderColor: isPending ? "var(--accent-route)" : "var(--border-subtle)",
          backgroundColor: isPending ? "rgba(34, 211, 238, 0.1)" : "transparent",
          color: isPending ? "var(--accent-route)" : "var(--fg-primary)",
        }}
        onClick={() => {
          if (!isOpen) setIsOpen(true);
          else setPendingSelection(isPending ? null : type);
        }}
      >
        <div className="flex flex-col text-left">
          <span className="text-[12px] font-semibold truncate w-44" title={currentName.primary}>
            <span className="text-[10px] uppercase font-normal text-[color:var(--fg-muted)] mr-1">{label}:</span> 
            {currentName.primary}
          </span>
          {currentName.secondary && (
            <span className="text-[10px] text-[color:var(--fg-secondary)] truncate w-44" title={currentName.secondary}>
              {currentName.secondary}
            </span>
          )}
          <span className="text-[9px] font-mono text-[color:var(--fg-muted)] mt-0.5">
            {lat.toFixed(2)}, {lon.toFixed(2)}
          </span>
        </div>
        <span className="text-[9px] uppercase mt-0.5">{isPending ? "Click map..." : "Set"}</span>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-[color:var(--bg-panel)] border border-[color:var(--border-subtle)] rounded shadow-lg">
          <div className="p-1">
            <input
              type="text"
              autoFocus
              className="w-full px-2 py-1 text-xs bg-[color:var(--bg-app)] border border-[color:var(--border-subtle)] rounded focus:outline-none focus:border-[color:var(--accent-route)] text-[color:var(--fg-primary)]"
              placeholder="Search ports..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <ul className="max-h-40 overflow-y-auto">
            {results.map((p, i) => (
              <li
                key={i}
                className="px-2 py-1 text-[11px] cursor-pointer hover:bg-[color:var(--accent-route)] hover:bg-opacity-20 transition-colors flex flex-col border-b border-[color:var(--border-subtle)] last:border-0"
                onClick={() => handleSelect(p)}
              >
                <span className="font-semibold">{p.name}</span>
                <span className="text-[9px] text-[color:var(--fg-muted)]">{p.country}</span>
              </li>
            ))}
            {query.length > 0 && results.length === 0 && (
              <li className="px-2 py-2 text-[10px] text-[color:var(--fg-muted)] text-center">
                No ports found.
              </li>
            )}
            {query.length === 0 && (
              <li className="px-2 py-2 text-[10px] text-[color:var(--fg-muted)] text-center">
                Type to search ports...
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
