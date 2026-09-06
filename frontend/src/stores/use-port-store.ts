import { create } from "zustand";

export interface Port {
  name: string;
  country: string;
  lat: number;
  lon: number;
}

interface PortState {
  ports: Port[];
  loading: boolean;
  error: string | null;
  fetchPorts: () => Promise<void>;
  searchPorts: (query: string) => Port[];
}

export const usePortStore = create<PortState>((set, get) => ({
  ports: [],
  loading: false,
  error: null,
  fetchPorts: async () => {
    if (get().ports.length > 0) return; // Already fetched
    set({ loading: true, error: null });
    try {
      // In development, Next.js rewrites to the FastAPI backend at :8000
      // Adjust if API URL is different
      const res = await fetch("http://localhost:8000/api/v1/ports");
      if (!res.ok) throw new Error("Failed to fetch ports");
      const data = await res.json();
      set({ ports: data, loading: false });
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },
  searchPorts: (query: string) => {
    const { ports } = get();
    if (!query) return [];
    const lower = query.toLowerCase();
    
    // Filter locally
    return ports
      .filter(p => 
        p.name.toLowerCase().includes(lower) || 
        p.country.toLowerCase().includes(lower)
      )
      .slice(0, 50); // Limit to 50 results
  }
}));
