import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { Nav } from "../components/Nav";
import { TitleCard } from "../components/Row";

export default function Search() {
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const q = sp.get("q") || "";
  const category = sp.get("category") || "";
  const language = sp.get("language") || "";
  const section = sp.get("section") || "";
  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const result = useQuery({
    queryKey: ["search", q, category, language, section],
    queryFn: () => api.search({ q, category, language, section }),
  });

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(sp);
    if (value) next.set(key, value);
    else next.delete(key);
    nav(`/search?${next}`);
  }

  const heading =
    section === "series"
      ? "TV Shows"
      : section === "songs"
        ? "Movies"
        : section === "minisodes"
          ? "New & Popular"
          : language === "hi" && !q && !category
            ? "Browse by Languages"
            : q
              ? `Results for “${q}”`
              : "Browse";

  return (
    <>
      <Nav q={q} />
      <div className="page">
        <h1>{heading}</h1>
        <div className="browse-filters">
          <label>
            Category
            <select value={category} onChange={(e) => setFilter("category", e.target.value)}>
              <option value="">All</option>
              {(meta.data?.categories || []).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label>
            Language
            <select value={language} onChange={(e) => setFilter("language", e.target.value)}>
              <option value="">All</option>
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
            </select>
          </label>
          <p className="muted filter-hint">Filters are applied on the server against the published catalogue.</p>
        </div>
        {result.isLoading && <p className="muted">Loading…</p>}
        {result.isError && <p className="err">{(result.error as Error).message}</p>}
        {result.data && result.data.count === 0 && (
          <div className="empty">
            <h2>Your search did not have any matches.</h2>
            <p>Try another keyword, category, or language — or go back to Home.</p>
          </div>
        )}
        {result.data && result.data.count > 0 && (
          <div className="grid">
            {result.data.shows.map((s) => (
              <TitleCard key={s.id} show={s} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
