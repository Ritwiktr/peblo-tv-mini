import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Nav } from "../components/Nav";
import { Row } from "../components/Row";

export default function Home() {
  const q = useQuery({ queryKey: ["catalog"], queryFn: api.catalog });
  if (q.isLoading) {
    return (
      <>
        <Nav />
        <div className="empty">Warming up the catalogue…</div>
      </>
    );
  }
  if (q.isError) {
    return (
      <>
        <Nav />
        <div className="err">
          {(q.error as Error).message || "Catalogue isn’t published yet."}
        </div>
      </>
    );
  }
  const cat = q.data!;
  const featured = cat.sections.find((s) => s.id === "featured")?.shows[0];
  const heroArt = featured?.artwork?.banner;

  return (
    <>
      <Nav />
      {featured && (
        <section className="hero" style={{ backgroundImage: heroArt ? `url(${heroArt})` : undefined }}>
          <div className="hero-inner">
            <div className="row-title">Featured</div>
            <h1>{featured.title}</h1>
            <p>{featured.synopsis}</p>
            <Link
              to={`/show/${featured.slug}`}
              style={{
                display: "inline-block",
                background: "var(--gold)",
                color: "#111",
                padding: "10px 18px",
                borderRadius: 999,
                fontWeight: 700,
              }}
            >
              Watch
            </Link>
          </div>
        </section>
      )}
      {cat.sections.map((s) => (
        <Row key={s.id} title={s.title} shows={s.shows} />
      ))}
    </>
  );
}
