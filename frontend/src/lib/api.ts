const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchRoutes() {
  const response = await fetch(`${API_BASE_URL}/api/v1/routes/`);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to fetch routes: ${response.status}`);
  }
  return response.json();
}

export async function fetchIcebergs() {
  const response = await fetch(`${API_BASE_URL}/api/v1/icebergs/detections`);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to fetch icebergs: ${response.status}`);
  }
  return response.json();
}

import { Vessel } from "./offshore-types";

export interface PaginationResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
}

export async function fetchVessels(country?: string): Promise<PaginationResponse<Vessel>> {
  const url = country ? `${API_BASE_URL}/api/v1/vessels/?country=${encodeURIComponent(country)}` : `${API_BASE_URL}/api/v1/vessels/`;
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to fetch vessels: ${response.status}`);
  }
  return response.json();
}

// Add more API wrappers here as needed
export async function fetchGlobalPorts() {
  const res = await fetch(`${API_BASE_URL}/api/v1/ports/?limit=6000`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to fetch all ports: ${res.status}`);
  }
  return res.json();
}

export async function searchPorts(query: string = "", skip = 0, limit = 50) {
  const url = query
    ? `${API_BASE_URL}/api/v1/ports/search?q=${encodeURIComponent(query)}&skip=${skip}&limit=${limit}`
    : `${API_BASE_URL}/api/v1/ports/?skip=${skip}&limit=${limit}`;
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to fetch ports: ${response.status}`);
  }
  return response.json();
}

export async function fetchLiveRouteEnvironment(waypoints: { lat: number, lon: number, eta?: string }[]) {
  const response = await fetch(`${API_BASE_URL}/api/v1/environment/live`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ waypoints })
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to fetch live environment: ${response.status}`);
  }
  return response.json();
}

export async function planRoute(request: any) {
  const response = await fetch(`${API_BASE_URL}/api/v1/routes/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      body?.detail ?? body?.error?.message ?? `Failed to plan route: ${response.status}`,
    );
  }
  return response.json();
}

export async function compareRoutes(request: any) {
  const response = await fetch(`${API_BASE_URL}/api/v1/routes/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      body?.detail ?? body?.error?.message ?? `Failed to compare routes: ${response.status}`,
    );
  }
  return response.json();
}
