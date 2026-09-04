import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, type Show } from "../api/client";
import { InfoIcon, MuteIcon, PlayIcon } from "../components/Icons";
import { Nav } from "../components/Nav";
import { Row, epCount } from "../components/Row";

function allShows(sections: { id: string; title: string; shows: Show[] }[]): Show[] {
  const seen = new Set<string>();
  const out: Show[] = [];
  for (const s of sections) {
    for (const show of s.shows) {
      if (seen.has(show.id)) continue;
      seen.add(show.id);
      out.push(show);
    }
  }
  return out;
}

function hasLanguage(show: Show, lang: string): boolean {
  if (show.trailer?.languages?.includes(lang)) return true;
  return show.seasons.some((s) => s.episodes.some((e) => e.languages?.includes(lang)));
}

export default function Home() {
  const q = useQuery({ queryKey: ["catalog"], queryFn: api.catalog });
  if (q.isLoading) {
    return (
      <>
        <Nav />
        <div className="billboard skeleton" />
        <div className="empty">Loading titles…</div>
      </>
    );
  }
  if (q.isError) {
    return (
      <>
        <Nav />
        <div className="empty">
          <h2>Nothing’s published yet</h2>
          <p>{(q.error as Error).message || "An admin needs to publish a catalogue from the CMS."}</p>
        </div>
      </>
    );
  }
  const cat = q.data!;
  const shows = allShows(cat.sections);
  const featured = cat.sections.find((s) => s.id === "featured")?.shows[0] || shows[0];
  const heroArt = featured?.artwork?.banner;
  const hindi = shows.filter((s) => hasLanguage(s, "hi"));
  const eps = featured ? epCount(featured) : 0;

  return (
    <>
      <Nav />
      {featured && (
        <section className="billboard">
          <div
            className="billboard-bg"
            style={{ backgroundImage: heroArt ? `url(${heroArt})` : undefined }}
          />
          <div className="billboard-vignette" />
          <div className="billboard-inner">
            <div className="billboard-kicker">
              <span className="n-badge">P</span> PEBLO ORIGINAL
            </div>
            <h1 className="billboard-title">{featured.title}</h1>
            <div className="billboard-facts">
              <span className="match">98% Match</span>
              <span>2026</span>
              <span className="rated">TV-Y7</span>
              <span>{eps || 1} Episodes</span>
              <span className="hd">HD</span>
            </div>
            <p className="billboard-syn">{featured.synopsis}</p>
            <div className="hero-actions">
              <Link to={`/show/${featured.slug}`} className="btn-play">
                <PlayIcon size={26} /> Play
              </Link>
              <Link to={`/show/${featured.slug}`} className="btn-info">
                <InfoIcon /> More Info
              </Link>
            </div>
          </div>
          <button className="hero-mute" aria-label="Mute">
            <MuteIcon />
          </button>
        </section>
      )}
      {!shows.length && (
        <div className="empty">
          <h2>The catalogue is empty</h2>
          <p>Publish from the CMS to populate these rows.</p>
        </div>
      )}
      <div className="rows">
        {shows.length > 0 && <Row title="Top picks" shows={shows} ranked />}
        {cat.sections.map((s) => (
          <Row key={s.id} title={s.title === "Featured" ? "Peblo Originals" : s.title} shows={s.shows} />
        ))}
        <Row title="Available in Hindi" shows={hindi} />
      </div>
      <footer className="nf-footer">
        <p>Questions? This is a Peblo TV demo catalogue — not affiliated with Netflix.</p>
        <div className="nf-foot-links">
          <span>Audio Description</span>
          <span>Help Centre</span>
          <span>Gift Cards</span>
          <span>Media Centre</span>
          <span>Investor Relations</span>
          <span>Jobs</span>
          <span>Terms of Use</span>
          <span>Privacy</span>
        </div>
        <button type="button" className="svc-code">
          Service Code
        </button>
        <p className="copy">© 2026 Peblo TV Mini</p>
      </footer>
    </>
  );
}
