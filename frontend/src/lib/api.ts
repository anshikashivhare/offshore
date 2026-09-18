export async function fetchRoutes() {
  const response = await fetch("/api/v1/routes/");
  if (!response.ok) {
    throw new Error(`Failed to fetch routes: ${response.status}`);
  }
  return response.json();
}

export async function fetchIcebergs() {
  const response = await fetch("/api/v1/icebergs/detections");
  if (!response.ok) {
    throw new Error(`Failed to fetch icebergs: ${response.status}`);
  }
  return response.json();
}

// Add more API wrappers here as needed
export async function fetchPorts() {
  const response = await fetch("/api/v1/ports/");
  if (!response.ok) {
    throw new Error(`Failed to fetch ports: ${response.status}`);
  }
  return response.json();
}

export async function fetchLiveRouteEnvironment(waypoints: { lat: number, lon: number, eta?: string }[]) {
  const response = await fetch("/api/v1/environment/live", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ waypoints })
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch live environment: ${response.status}`);
  }
  return response.json();
}

export async function planRoute(request: any) {
  const response = await fetch("/api/v1/routes/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });
  if (!response.ok) {
    throw new Error(`Failed to plan route: ${response.status}`);
  }
  return response.json();
}
