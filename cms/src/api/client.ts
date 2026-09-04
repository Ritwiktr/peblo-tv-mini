const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  return localStorage.getItem("peblo_token");
}
export function setToken(t: string | null) {
  if (t) localStorage.setItem("peblo_token", t);
  else localStorage.removeItem("peblo_token");
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API}${path}`, { ...init, headers });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!res.ok) {
    const d = data as { detail?: unknown };
    let msg = res.statusText;
    if (typeof d.detail === "string") msg = d.detail;
    else if (d.detail && typeof d.detail === "object" && "message" in (d.detail as object)) {
      msg = String((d.detail as { message: string }).message);
    } else if (Array.isArray(d.detail)) {
      msg = d.detail.map((x: { msg?: string }) => x.msg).join("; ");
    }
    const err = new Error(msg) as Error & { status: number };
    err.status = res.status;
    throw err;
  }
  return data as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; role: string; email: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ id: string; email: string; role: string }>("/auth/me"),
  reference: () =>
    request<{
      sections: string[];
      categories: string[];
      languages: string[];
      artwork_specs: Record<string, { aspect: string; target_px: number[]; max_kb: number }>;
    }>("/admin/reference"),
  shows: (params: Record<string, string | number | undefined>) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") q.set(k, String(v));
    });
    return request<{ items: Show[]; total: number; page: number; page_size: number }>(
      `/admin/shows?${q}`
    );
  },
  show: (id: string) => request<Show>(`/admin/shows/${id}`),
  createShow: (body: Partial<Show>) =>
    request<Show>("/admin/shows", { method: "POST", body: JSON.stringify(body) }),
  patchShow: (id: string, body: Partial<Show>) =>
    request<Show>(`/admin/shows/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  episodes: (showId: string, params: Record<string, string> = {}) => {
    const q = new URLSearchParams(params);
    return request<Episode[]>(`/admin/shows/${showId}/episodes?${q}`);
  },
  createEpisode: (showId: string, body: Partial<Episode>) =>
    request<Episode>(`/admin/shows/${showId}/episodes`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchEpisode: (id: string, body: Partial<Episode>) =>
    request<Episode>(`/admin/episodes/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  uploadShowArt: (showId: string, kind: string, file: File) => {
    const fd = new FormData();
    fd.append("kind", kind);
    fd.append("file", file);
    return request<Art>(`/admin/shows/${showId}/artwork`, { method: "POST", body: fd });
  },
  uploadEpisodeArt: (episodeId: string, kind: string, file: File) => {
    const fd = new FormData();
    fd.append("kind", kind);
    fd.append("file", file);
    return request<Art>(`/admin/episodes/${episodeId}/artwork`, { method: "POST", body: fd });
  },
  validation: () => request<ValidationReport>("/admin/validation-report"),
  publish: () => request<PublishRun>("/admin/catalog/publish", { method: "POST" }),
  runs: () => request<PublishRun[]>("/admin/catalog/runs"),
  rollback: (id: string) =>
    request<PublishRun>(`/admin/catalog/runs/${id}/rollback`, { method: "POST" }),
};

export type Art = { id: string; kind: string; url: string; width: number; height: number; byte_size: number };
export type Show = {
  id: string;
  slug: string;
  title: string;
  synopsis: string;
  section: string | null;
  categories: string[];
  status: string;
  episode_count: number;
  artwork: Art[];
};
export type Episode = {
  id: string;
  title: string;
  season_number: number;
  episode_number: number;
  duration_seconds: number | null;
  language: string;
  content_group: string;
  status: string;
  artwork: Art[];
};
export type ValidationReport = {
  can_publish: boolean;
  clean?: boolean;
  blocking_count: number;
  blocking: { code: string; message: string }[];
  warnings: { code: string; message: string }[];
  ingest_warnings?: { code: string; message: string }[];
  by_show: { show_id: string; title: string; issues: { message: string }[] }[];
  preview?: { show_count: number; episode_count: number; sections: { id: string; title: string; show_count: number }[] };
  hint: string;
};
export type PublishRun = {
  id: string;
  status: string;
  show_count: number;
  episode_count: number;
  warnings: string[];
  error_message: string | null;
  triggered_by: string | null;
  started_at: string;
  finished_at: string | null;
};
