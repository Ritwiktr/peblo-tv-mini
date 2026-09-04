import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, type Show } from "../api/client";
import { PlayIcon } from "../components/Icons";
import { Nav } from "../components/Nav";
import { epCount } from "../components/Row";

export default function ShowDetail() {
  const { slug } = useParams();
  const q = useQuery({
    queryKey: ["show", slug],
    queryFn: () => api.show(slug!),
    enabled: !!slug,
  });

  if (q.isLoading) {
    return (
      <>
        <Nav />
        <div className="empty">Loading…</div>
      </>
    );
  }
  if (!q.data) {
    return (
      <>
        <Nav />
        <div className="empty">
          <h2>This title isn’t available</h2>
          <p>It isn’t in the published catalogue.</p>
        </div>
      </>
    );
  }

  const show = q.data;
  const banner = show.artwork?.banner;
  const eps = epCount(show);
  return (
    <>
      <Nav />
      <section className="billboard detail-hero">
        <div className="billboard-bg" style={{ backgroundImage: banner ? `url(${banner})` : undefined }} />
        <div className="billboard-vignette" />
        <div className="billboard-inner">
          <div className="billboard-kicker">
            <span className="n-badge">P</span> PEBLO ORIGINAL
          </div>
          <h1 className="billboard-title">{show.title}</h1>
          <div className="billboard-facts">
            <span className="match">97% Match</span>
            <span>2026</span>
            <span className="rated">TV-Y7</span>
            <span>{eps} Episodes</span>
            <span className="hd">HD</span>
          </div>
          <p className="billboard-syn">{show.synopsis}</p>
          <div style={{ marginBottom: 16 }}>
            {(show.categories || []).map((c) => (
              <span className="chip" key={c}>
                {c}
              </span>
            ))}
          </div>
          <div className="hero-actions">
            <a className="btn-play" href="#episodes">
              <PlayIcon size={26} /> Play
            </a>
            {show.trailer && (
              <a className="btn-info" href="#trailer">
                Trailer
              </a>
            )}
          </div>
        </div>
      </section>
      <div className="page" style={{ paddingTop: 12 }} id="episodes">
        {show.trailer && (
          <section id="trailer">
            <h2 className="row-title" style={{ marginLeft: 0 }}>
              Trailer
            </h2>
            <p className="muted">Season 0 is reserved for trailers.</p>
            <div className="ep-list">
              <EpisodeCard ep={show.trailer} index={0} />
            </div>
          </section>
        )}
        {show.seasons.map((season) => (
          <section key={season.season_number}>
            <h2 className="row-title" style={{ marginLeft: 0 }}>
              Season {season.season_number}
              <span className="muted"> · {season.episodes.length} Episodes</span>
            </h2>
            <div className="ep-list">
              {season.episodes.map((ep, i) => (
                <EpisodeCard key={ep.content_group} ep={ep} index={i} />
              ))}
            </div>
          </section>
        ))}
        <p>
          <Link to="/" className="muted">
            ‹ Back to Home
          </Link>
        </p>
      </div>
    </>
  );
}

function EpisodeCard({
  ep,
  index,
}: {
  ep: Show["seasons"][0]["episodes"][0] | NonNullable<Show["trailer"]>;
  index: number;
}) {
  const [lang, setLang] = useState(ep.languages.includes("en") ? "en" : ep.languages[0]);
  const variant = ep.variants?.find((v) => v.language === lang);
  const thumb = ep.artwork?.thumbnail;
  const mins = Math.round((variant?.duration_seconds || ep.duration_seconds) / 60);
  const num = ep.episode_number || index + 1;
  return (
    <article className="ep-row">
      <div className="ep-num">{num}</div>
      {thumb ? <img src={thumb} alt="" loading="lazy" /> : <div className="ep-ph" />}
      <div>
        <div className="ep-title">{variant?.title || ep.title}</div>
        <div className="muted">
          {ep.languages.map((l) => (
            <button key={l} className={`lang-btn ${l === lang ? "on" : ""}`} onClick={() => setLang(l)}>
              {l === "hi" ? "हिन्दी" : "English"}
            </button>
          ))}
        </div>
      </div>
      <div className="muted">{mins}m</div>
    </article>
  );
}
