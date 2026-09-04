import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Empty, ErrorBox, Loading, StatusPill } from "../components/Layout";

export default function Shows() {
  const [q, setQ] = useState("");
  const [section, setSection] = useState("");
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("");
  const [page, setPage] = useState(1);
  const ref = useQuery({ queryKey: ["ref"], queryFn: api.reference });
  const shows = useQuery({
    queryKey: ["shows", q, section, status, language, page],
    queryFn: () => api.shows({ q, section, status, language, page, page_size: 12 }),
  });
  const total = shows.data?.total ?? 0;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Shows</h1>
          <p className="lede">
            {total ? `${total} title${total === 1 ? "" : "s"} in the library.` : "Catalogue titles editors can fix and publish."}
          </p>
        </div>
        <Link to="/shows/new" className="btn accent">
          New show
        </Link>
      </div>
      <div className="card toolbar">
        <div className="row">
          <div className="field grow">
            <label htmlFor="show-q">Search</label>
            <input
              id="show-q"
              placeholder="Title or synopsis"
              value={q}
              onChange={(e) => {
                setPage(1);
                setQ(e.target.value);
              }}
            />
          </div>
          <div className="field">
            <label htmlFor="show-section">Section</label>
            <select
              id="show-section"
              value={section}
              onChange={(e) => {
                setPage(1);
                setSection(e.target.value);
              }}
            >
              <option value="">All</option>
              {(ref.data?.sections || []).map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="show-status">Status</label>
            <select
              id="show-status"
              value={status}
              onChange={(e) => {
                setPage(1);
                setStatus(e.target.value);
              }}
            >
              <option value="">All</option>
              <option value="published">published</option>
              <option value="draft">draft</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="show-lang">Language</label>
            <select
              id="show-lang"
              value={language}
              onChange={(e) => {
                setPage(1);
                setLanguage(e.target.value);
              }}
            >
              <option value="">All</option>
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
            </select>
          </div>
        </div>
      </div>
      {shows.isLoading && <Loading />}
      {shows.isError && <ErrorBox error={shows.error} />}
      {shows.data && shows.data.items.length === 0 && (
        <Empty>
          No shows match those filters.
          <div style={{ marginTop: 12 }}>
            <Link to="/shows/new" className="btn">
              Create a show
            </Link>
          </div>
        </Empty>
      )}
      {shows.data && shows.data.items.length > 0 && (
        <>
          <div className="show-list">
            {shows.data.items.map((s) => {
              const poster = s.artwork?.find((a) => a.kind === "poster");
              return (
                <Link key={s.id} className="show-item" to={`/shows/${s.id}`}>
                  <div className="show-poster">
                    {poster ? <img src={poster.url} alt="" /> : "No art"}
                  </div>
                  <div>
                    <h3>{s.title}</h3>
                    <div className="meta">
                      <span className="muted">{s.section || "No section"}</span>
                      <span className="muted">·</span>
                      <span className="muted">{s.slug}</span>
                    </div>
                  </div>
                  <span className="ep-count">{s.episode_count} episodes</span>
                  <StatusPill status={s.status} />
                </Link>
              );
            })}
          </div>
          <div className="pager">
            <button type="button" className="btn secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              Previous
            </button>
            <span className="muted">
              Page {page} of {Math.max(1, Math.ceil(shows.data.total / shows.data.page_size))}
            </span>
            <button
              type="button"
              className="btn secondary"
              disabled={page * shows.data.page_size >= shows.data.total}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </>
  );
}
