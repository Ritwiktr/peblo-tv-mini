import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { Nav } from "../components/Nav";
import { PosterCard } from "../components/Row";

export default function Search() {
  const [sp] = useSearchParams();
  const q = sp.get("q") || "";
  const category = sp.get("category") || "";
  const language = sp.get("language") || "";
  const result = useQuery({
    queryKey: ["search", q, category, language],
    queryFn: () => api.search({ q, category, language }),
  });

  return (
    <>
      <Nav q={q} category={category} language={language} />
      <div className="page">
        <h1>Search</h1>
        <p className="muted">
          {q && <>“{q}” · </>}
          {category || "any category"} · {language || "any language"}
        </p>
        {result.isLoading && <p className="muted">Searching…</p>}
        {result.isError && <p className="err">{(result.error as Error).message}</p>}
        {result.data && result.data.count === 0 && (
          <div className="empty">
            <h2>Nothing here yet</h2>
            <p>Try a shorter word, or clear a filter. Search looks at show titles, episode titles, and categories.</p>
          </div>
        )}
        {result.data && result.data.count > 0 && (
          <div className="scroller" style={{ flexWrap: "wrap" }}>
            {result.data.shows.map((s) => (
              <PosterCard key={s.id} show={s} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
