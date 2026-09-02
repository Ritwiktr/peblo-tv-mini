import { useState } from "react";
import { Link } from "react-router-dom";
import type { Show } from "../api/client";

export function PosterCard({ show }: { show: Show }) {
  const src = show.artwork?.poster;
  const [on, setOn] = useState(false);
  return (
    <Link to={`/show/${show.slug}`} className="poster" style={{ backgroundImage: src ? `url(${src})` : undefined }}>
      {!on && <div className="ph" />}
      {src && (
        <img
          src={src}
          alt={show.title}
          loading="lazy"
          className={on ? "on" : ""}
          onLoad={() => setOn(true)}
        />
      )}
      <div className="cap">{show.title}</div>
    </Link>
  );
}

export function Row({ title, shows }: { title: string; shows: Show[] }) {
  if (!shows.length) return null;
  return (
    <section className="row-wrap">
      <h2 className="row-title">{title}</h2>
      <div className="scroller">
        {shows.map((s) => (
          <PosterCard key={s.id} show={s} />
        ))}
      </div>
    </section>
  );
}
