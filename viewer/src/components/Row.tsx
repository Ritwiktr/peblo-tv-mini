import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import type { Show } from "../api/client";
import { ChevronDown, LikeIcon, PlayIcon, PlusIcon } from "./Icons";

export function epCount(show: Show): number {
  return (show.seasons || []).reduce((n, s) => n + s.episodes.length, 0);
}

function matchPct(id: string): number {
  let n = 0;
  for (const c of id) n += c.charCodeAt(0);
  return 86 + (n % 13);
}

function PosterArt({ show }: { show: Show }) {
  const src = show.artwork?.poster;
  const [on, setOn] = useState(false);
  return (
    <>
      {src ? (
        <>
          {!on && <div className="ph" />}
          <img src={src} alt="" loading="lazy" className={on ? "on" : ""} onLoad={() => setOn(true)} />
        </>
      ) : (
        <div className="art-fallback" aria-hidden="true" />
      )}
      <div className="card-name">{show.title}</div>
    </>
  );
}

export function TitleCard({ show }: { show: Show }) {
  const eps = epCount(show);
  return (
    <div className="tcard">
      <Link to={`/show/${show.slug}`} className="tcard-scale" aria-label={show.title}>
        <div className="tcard-art">
          <PosterArt show={show} />
        </div>
        <div className="tcard-extra">
          <div className="tcard-btns">
            <span className="round fill">
              <PlayIcon size={16} />
            </span>
            <span className="round">
              <PlusIcon />
            </span>
            <span className="round">
              <LikeIcon />
            </span>
            <span className="round push">
              <ChevronDown />
            </span>
          </div>
          <div className="tcard-showname">{show.title}</div>
          <div className="tcard-meta">
            <span className="match">{matchPct(show.id)}% Match</span>
            <span className="rated">TV-Y7</span>
            <span>{eps || 1} Episodes</span>
            <span className="hd">HD</span>
          </div>
          <div className="tcard-tags">{(show.categories || []).slice(0, 3).join(" · ")}</div>
        </div>
      </Link>
    </div>
  );
}

export function PosterCard({ show, rank }: { show: Show; rank?: number }) {
  return (
    <Link to={`/show/${show.slug}`} className="poster" aria-label={show.title}>
      {rank !== undefined && <span className="rank">{rank}</span>}
      <div className="poster-art">
        <PosterArt show={show} />
      </div>
    </Link>
  );
}

export function Row({
  title,
  shows,
  ranked,
}: {
  title: string;
  shows: Show[];
  ranked?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  if (!shows.length) return null;

  function slide(dir: number) {
    const el = ref.current;
    if (!el) return;
    el.scrollBy({ left: dir * el.clientWidth * 0.92, behavior: "smooth" });
  }

  return (
    <section className={`row-wrap ${ranked ? "top10" : ""}`}>
      <h2 className="row-title">
        {title} <span className="see-all">Explore All ›</span>
      </h2>
      <button className="row-arrow left" aria-label="Previous" onClick={() => slide(-1)}>
        ‹
      </button>
      <div className="scroller" ref={ref}>
        {ranked
          ? shows.map((s, i) => <PosterCard key={s.id} show={s} rank={i + 1} />)
          : shows.map((s) => <TitleCard key={s.id} show={s} />)}
      </div>
      <button className="row-arrow right" aria-label="Next" onClick={() => slide(1)}>
        ›
      </button>
    </section>
  );
}
