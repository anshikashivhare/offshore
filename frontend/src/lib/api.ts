export async function fetchRoutes() {
  const response = await fetch("/api/v1/routes/");
  if (!response.ok) {
    throw new Error(`Failed to fetch routes: ${response.status}`);
  }
  return response.json();
}

export async function fetchIcebergs() {
  const response = await fetch("/api/v1/icebergs/");
  if (!response.ok) {
    throw new Error(`Failed to fetch icebergs: ${response.status}`);
  }
  return response.json();
}

// Add more API wrappers here as needed
