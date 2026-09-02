import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api, type Show } from "../api/client";
import { Nav } from "../components/Nav";

function flatten(cat: { sections: { shows: Show[] }[] }): Show[] {
  return cat.sections.flatMap((s) => s.shows);
}

export default function ShowDetail() {
  const { slug } = useParams();
  const q = useQuery({ queryKey: ["catalog"], queryFn: api.catalog });
  const show = useMemo(
    () => (q.data ? flatten(q.data).find((s) => s.slug === slug) : undefined),
    [q.data, slug]
  );

  if (q.isLoading) {
    return (
      <>
        <Nav />
        <div className="empty">Loading show…</div>
      </>
    );
  }
  if (!show) {
    return (
      <>
        <Nav />
        <div className="empty">
          <h2>We couldn’t find that show</h2>
          <p>It may not have been published yet.</p>
        </div>
      </>
    );
  }

  const banner = show.artwork?.banner;
  return (
    <>
      <Nav />
      <section className="hero" style={{ minHeight: "42vh", backgroundImage: banner ? `url(${banner})` : undefined }}>
        <div className="hero-inner">
          <h1>{show.title}</h1>
          <p>{show.synopsis}</p>
          <div>
            {show.categories.map((c) => (
              <span className="chip" key={c}>
                {c}
              </span>
            ))}
          </div>
        </div>
      </section>
      <div className="page">
        {show.trailer && (
          <>
            <h2>Trailer</h2>
            <p className="muted">Season 0 — not listed with the regular seasons.</p>
            <EpisodeCard ep={show.trailer} />
          </>
        )}
        {show.seasons.map((season) => (
          <section key={season.season_number}>
            <h2>Season {season.season_number}</h2>
            <div className="thumbs">
              {season.episodes.map((ep) => (
                <EpisodeCard key={ep.content_group} ep={ep} />
              ))}
            </div>
          </section>
        ))}
        {show.seasons.length === 0 && !show.trailer && (
          <div className="empty">No episodes in the published catalogue yet.</div>
        )}
      </div>
    </>
  );
}

function EpisodeCard({ ep }: { ep: Show["seasons"][0]["episodes"][0] | NonNullable<Show["trailer"]> }) {
  const [lang, setLang] = useState(ep.languages.includes("en") ? "en" : ep.languages[0]);
  const variant = ep.variants?.find((v) => v.language === lang);
  const thumb = ep.artwork?.thumbnail;
  const mins = Math.round((variant?.duration_seconds || ep.duration_seconds) / 60);
  return (
    <article className="thumb">
      {thumb ? <img src={thumb} alt="" loading="lazy" /> : <div style={{ aspectRatio: "16/9", background: "#1a2b42" }} />}
      <div className="meta">
        <strong>
          {ep.episode_number ? `E${ep.episode_number} · ` : ""}
          {variant?.title || ep.title}
        </strong>
        <div className="muted">{mins} min</div>
        <div style={{ marginTop: 6 }}>
          {ep.languages.map((l) => (
            <button
              key={l}
              className="chip"
              onClick={() => setLang(l)}
              style={{
                border: 0,
                cursor: "pointer",
                background: l === lang ? "var(--gold)" : "#1f3d3a",
                color: l === lang ? "#111" : "var(--teal)",
              }}
            >
              {l === "hi" ? "हिन्दी" : "English"}
            </button>
          ))}
        </div>
      </div>
    </article>
  );
}
