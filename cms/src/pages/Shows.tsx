import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Empty, ErrorBox, Loading } from "../components/Layout";

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

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>Shows</h1>
        <Link to="/shows/new" className="btn" style={{ textDecoration: "none" }}>
          New show
        </Link>
      </div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="row">
          <div style={{ flex: 2 }}>
            <label>Search</label>
            <input
              placeholder="Title or synopsis"
              value={q}
              onChange={(e) => {
                setPage(1);
                setQ(e.target.value);
              }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label>Section</label>
            <select
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
          <div style={{ flex: 1 }}>
            <label>Status</label>
            <select
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
          <div style={{ flex: 1 }}>
            <label>Language</label>
            <select
              value={language}
              onChange={(e) => {
                setPage(1);
                setLanguage(e.target.value);
              }}
            >
              <option value="">All</option>
              <option value="en">en</option>
              <option value="hi">hi</option>
            </select>
          </div>
        </div>
      </div>
      {shows.isLoading && <Loading />}
      {shows.isError && <ErrorBox error={shows.error} />}
      {shows.data && shows.data.items.length === 0 && (
        <Empty>No shows match those filters. Try clearing search, or create a new show.</Empty>
      )}
      {shows.data && shows.data.items.length > 0 && (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Section</th>
                <th>Status</th>
                <th>Episodes</th>
              </tr>
            </thead>
            <tbody>
              {shows.data.items.map((s) => (
                <tr key={s.id}>
                  <td>
                    <Link to={`/shows/${s.id}`}>{s.title}</Link>
                    <div className="muted">{s.slug}</div>
                  </td>
                  <td>{s.section || "—"}</td>
                  <td>
                    <span className={`pill ${s.status}`}>{s.status}</span>
                  </td>
                  <td>{s.episode_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pager">
            <button className="btn secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              Previous
            </button>
            <span className="muted">
              Page {page} of {Math.max(1, Math.ceil(shows.data.total / shows.data.page_size))} ·{" "}
              {shows.data.total} shows
            </span>
            <button
              className="btn secondary"
              disabled={page * shows.data.page_size >= shows.data.total}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </>
  );
}
