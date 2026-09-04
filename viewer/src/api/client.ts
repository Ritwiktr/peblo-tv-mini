const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  return res.json();
}

export type Art = { poster?: string; banner?: string; thumbnail?: string };
export type Episode = {
  content_group: string;
  episode_number: number;
  title: string;
  duration_seconds: number;
  languages: string[];
  artwork: Art;
  variants?: { language: string; title: string; duration_seconds: number }[];
};
export type Show = {
  id: string;
  slug: string;
  title: string;
  synopsis: string;
  categories: string[];
  section: string;
  artwork: Art;
  trailer: Episode | null;
  seasons: { season_number: number; episodes: Episode[] }[];
};
export type Catalogue = {
  published_at: string;
  show_count: number;
  episode_count: number;
  sections: { id: string; title: string; shows: Show[] }[];
};

export const api = {
  catalog: () => get<Catalogue>("/catalog"),
  meta: () => get<{ sections: string[]; categories: string[]; languages: string[] }>("/catalog/meta"),
  show: (slug: string) => get<Show>(`/catalog/shows/${slug}`),
  search: (params: Record<string, string>) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v) q.set(k, v);
    });
    return get<{ count: number; shows: Show[] }>(`/catalog/search?${q}`);
  },
};
