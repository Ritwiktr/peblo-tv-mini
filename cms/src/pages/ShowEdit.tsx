import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, type Episode, type Show } from "../api/client";
import { ArtworkSlot } from "../components/ArtworkSlot";
import { Empty, ErrorBox, Loading, StatusPill } from "../components/Layout";

export default function ShowEdit() {
  const { id } = useParams();
  const isNew = id === "new" || !id;
  const nav = useNavigate();
  const qc = useQueryClient();
  const showQ = useQuery({
    queryKey: ["show", id],
    queryFn: () => api.show(id!),
    enabled: !isNew,
  });
  const ref = useQuery({ queryKey: ["ref"], queryFn: api.reference });
  const [form, setForm] = useState<Partial<Show>>({
    title: "",
    synopsis: "",
    section: "series",
    status: "draft",
    categories: [],
  });
  const [saveErr, setSaveErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (showQ.data) setForm(showQ.data);
  }, [showQ.data]);

  const save = async () => {
    setSaveErr(null);
    setSaving(true);
    try {
      if (isNew) {
        const created = await api.createShow(form);
        nav(`/shows/${created.id}`);
      } else {
        await api.patchShow(id!, {
          title: form.title,
          synopsis: form.synopsis,
          section: form.section,
          status: form.status,
          categories: form.categories,
        });
        qc.invalidateQueries({ queryKey: ["show", id] });
      }
    } catch (e) {
      setSaveErr((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  if (!isNew && showQ.isLoading) return <Loading />;
  if (!isNew && showQ.isError) return <ErrorBox error={showQ.error} />;

  const cats = form.categories || [];

  return (
    <>
      <p className="crumb">
        <Link to="/">Shows</Link> / {isNew ? "New" : form.title || "Edit"}
      </p>
      <div className="page-head">
        <div>
          <h1>{isNew ? "New show" : form.title || "Edit show"}</h1>
          <p className="lede">
            {isNew
              ? "Set status to published and pick a section, then save — it will be listed on Peblo TV."
              : "Published + a section lists this title on Peblo TV when you save. Artwork is optional."}
          </p>
        </div>
        <div className="sticky-actions">
          {!isNew && <StatusPill status={form.status || "draft"} />}
          <button type="button" className="btn accent" onClick={() => void save()} disabled={saving || !form.title}>
            {saving ? "Saving…" : isNew ? "Create show" : "Save changes"}
          </button>
        </div>
      </div>
      {saveErr && <div className="banner error">{saveErr}</div>}
      <div className="edit-grid">
        <div className="card">
          <p>
            <label htmlFor="title">Title</label>
            <input
              id="title"
              value={form.title || ""}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </p>
          <p>
            <label htmlFor="synopsis">Synopsis</label>
            <textarea
              id="synopsis"
              value={form.synopsis || ""}
              onChange={(e) => setForm({ ...form, synopsis: e.target.value })}
            />
          </p>
          <div className="row">
            <div className="field">
              <label htmlFor="section">Section</label>
              <select
                id="section"
                value={form.section || ""}
                onChange={(e) => setForm({ ...form, section: e.target.value || null })}
              >
                <option value="">(none — required before publish)</option>
                {(ref.data?.sections || []).map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="status">Status</label>
              <select
                id="status"
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              >
                <option value="draft">draft</option>
                <option value="published">published</option>
              </select>
            </div>
          </div>
          <p>
            <label>Categories</label>
            <div className="chips">
              {(ref.data?.categories || []).map((c) => {
                const on = cats.includes(c);
                return (
                  <button
                    key={c}
                    type="button"
                    className={`chip ${on ? "on" : ""}`}
                    onClick={() =>
                      setForm({
                        ...form,
                        categories: on ? cats.filter((x) => x !== c) : [...cats, c],
                      })
                    }
                  >
                    {c}
                  </button>
                );
              })}
            </div>
          </p>
        </div>
        <div>
          {isNew ? (
            <div className="card">
              <h2 style={{ marginTop: 0 }}>Artwork</h2>
              <p className="muted">Create the show first — then you’ll get poster, banner, and thumbnail slots here.</p>
            </div>
          ) : (
            showQ.data && (
              <>
                <h2 style={{ marginTop: 0 }}>Artwork</h2>
                <p className="muted" style={{ marginTop: 0 }}>
                  Checked on the server. Wrong ratio or oversized files come back with a reason you can act on.
                </p>
                <div className="slots">
                  {(["poster", "banner", "thumbnail"] as const).map((kind) => (
                    <ArtworkSlot
                      key={kind}
                      kind={kind}
                      current={showQ.data.artwork.find((a) => a.kind === kind)}
                      onUpload={async (file) => {
                        await api.uploadShowArt(showQ.data.id, kind, file);
                        qc.invalidateQueries({ queryKey: ["show", id] });
                      }}
                    />
                  ))}
                </div>
              </>
            )
          )}
        </div>
      </div>
      {!isNew && showQ.data && <Episodes showId={showQ.data.id} />}
    </>
  );
}

function Episodes({ showId }: { showId: string }) {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [language, setLanguage] = useState("");
  const [status, setStatus] = useState("");
  const eps = useQuery({
    queryKey: ["eps", showId, q, language, status],
    queryFn: () => api.episodes(showId, { q, language, status }),
  });
  const [draft, setDraft] = useState<Partial<Episode>>({
    title: "",
    season_number: 1,
    episode_number: 1,
    language: "en",
    duration_seconds: 300,
    status: "draft",
  });
  const create = useMutation({
    mutationFn: () => api.createEpisode(showId, draft),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["eps", showId] });
      setDraft({ ...draft, title: "", episode_number: (draft.episode_number || 1) + 1 });
    },
  });
  const grouped = useMemo(() => {
    const m = new Map<number, Episode[]>();
    for (const ep of eps.data || []) {
      const arr = m.get(ep.season_number) || [];
      arr.push(ep);
      m.set(ep.season_number, arr);
    }
    return [...m.entries()].sort((a, b) => a[0] - b[0]);
  }, [eps.data]);

  return (
    <>
      <div className="page-head" style={{ marginTop: 28, marginBottom: 8 }}>
        <h2 style={{ margin: 0 }}>Episodes</h2>
      </div>
      <div className="card toolbar">
        <div className="row">
          <div className="field grow">
            <label htmlFor="ep-q">Search episodes</label>
            <input id="ep-q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Title" />
          </div>
          <div className="field">
            <label>Language</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="">All</option>
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
            </select>
          </div>
          <div className="field">
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All</option>
              <option value="published">published</option>
              <option value="draft">draft</option>
            </select>
          </div>
        </div>
      </div>
      {eps.isLoading && <Loading />}
      {eps.isError && <ErrorBox error={eps.error} />}
      {eps.data && eps.data.length === 0 && <Empty>No episodes yet. Add one below.</Empty>}
      {grouped.map(([season, rows]) => (
        <div key={season}>
          <div className="season-label">{season === 0 ? "Trailer · season 0" : `Season ${season}`}</div>
          {rows.map((ep) => (
            <EpisodeRow key={ep.id} ep={ep} showId={showId} />
          ))}
        </div>
      ))}
      <h3>Add episode</h3>
      {create.isError && <ErrorBox error={create.error} />}
      <div className="card">
        <div className="row">
          <div className="field grow">
            <label>Title</label>
            <input value={draft.title || ""} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
          </div>
          <div className="field">
            <label>Season</label>
            <input
              type="number"
              value={draft.season_number}
              onChange={(e) => setDraft({ ...draft, season_number: Number(e.target.value) })}
            />
          </div>
          <div className="field">
            <label>Episode #</label>
            <input
              type="number"
              value={draft.episode_number}
              onChange={(e) => setDraft({ ...draft, episode_number: Number(e.target.value) })}
            />
          </div>
          <div className="field">
            <label>Language</label>
            <select value={draft.language} onChange={(e) => setDraft({ ...draft, language: e.target.value })}>
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
            </select>
          </div>
          <div className="field">
            <label>Duration (sec)</label>
            <input
              type="number"
              value={draft.duration_seconds ?? ""}
              onChange={(e) => setDraft({ ...draft, duration_seconds: Number(e.target.value) })}
            />
          </div>
        </div>
        <p className="muted">Season 0 is reserved for trailers and won’t show as a normal season in the viewer.</p>
        <button
          type="button"
          className="btn"
          disabled={create.isPending || !draft.title}
          onClick={() => create.mutate()}
        >
          Add episode
        </button>
      </div>
    </>
  );
}

function EpisodeRow({ ep, showId }: { ep: Episode; showId: string }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState(ep.title);
  const [status, setStatus] = useState(ep.status);
  const [duration, setDuration] = useState(ep.duration_seconds);
  const [err, setErr] = useState<string | null>(null);
  const mins = ep.duration_seconds ? Math.round(ep.duration_seconds / 60) : null;
  const thumb = ep.artwork.find((a) => a.kind === "thumbnail");

  return (
    <div className="card ep-card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ alignItems: "center", flex: 1 }}>
          <div className="show-poster" style={{ width: 72, height: 40, borderRadius: 6 }}>
            {thumb ? <img src={thumb.url} alt="" /> : <span>No thumb</span>}
          </div>
          <div>
            <strong>
              {ep.season_number === 0 ? "Trailer" : `S${ep.season_number}E${ep.episode_number}`} · {ep.title}
            </strong>
            <div className="meta">
              <span className="lang">{ep.language === "hi" ? "HI" : "EN"}</span>
              <span className="muted">{mins != null ? `${mins} min` : "no duration"}</span>
              <span className="muted">{ep.content_group}</span>
              <StatusPill status={ep.status} />
            </div>
          </div>
        </div>
        <button type="button" className="btn secondary" onClick={() => setOpen(!open)}>
          {open ? "Close" : "Edit & artwork"}
        </button>
      </div>
      {open && (
        <>
          {err && <div className="banner error">{err}</div>}
          <div className="row" style={{ marginTop: 12 }}>
            <div className="field grow">
              <label>Title</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="field">
              <label>Duration (sec)</label>
              <input type="number" value={duration ?? ""} onChange={(e) => setDuration(Number(e.target.value))} />
            </div>
            <div className="field">
              <label>Status</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="draft">draft</option>
                <option value="published">published</option>
              </select>
            </div>
          </div>
          <button
            type="button"
            className="btn"
            style={{ margin: "12px 0" }}
            onClick={async () => {
              setErr(null);
              try {
                await api.patchEpisode(ep.id, { title, status, duration_seconds: duration });
                qc.invalidateQueries({ queryKey: ["eps", showId] });
              } catch (e) {
                setErr((e as Error).message);
              }
            }}
          >
            Save episode
          </button>
          <div className="slots triple">
            {(["poster", "banner", "thumbnail"] as const).map((kind) => (
              <ArtworkSlot
                key={kind}
                kind={kind}
                current={ep.artwork.find((a) => a.kind === kind)}
                onUpload={async (file) => {
                  await api.uploadEpisodeArt(ep.id, kind, file);
                  qc.invalidateQueries({ queryKey: ["eps", showId] });
                }}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
