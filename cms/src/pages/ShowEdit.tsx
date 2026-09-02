import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, type Episode, type Show } from "../api/client";
import { ArtworkSlot } from "../components/ArtworkSlot";
import { Empty, ErrorBox, Loading } from "../components/Layout";

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

  useEffect(() => {
    if (showQ.data) setForm(showQ.data);
  }, [showQ.data]);

  const save = async () => {
    setSaveErr(null);
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
    }
  };

  if (!isNew && showQ.isLoading) return <Loading />;
  if (!isNew && showQ.isError) return <ErrorBox error={showQ.error} />;

  return (
    <>
      <p className="muted">
        <Link to="/">Shows</Link> / {isNew ? "New" : form.title}
      </p>
      <h1>{isNew ? "New show" : "Edit show"}</h1>
      {saveErr && <div className="banner error">{saveErr}</div>}
      <div className="card">
        <p>
          <label>Title</label>
          <input value={form.title || ""} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </p>
        <p>
          <label>Synopsis</label>
          <textarea
            value={form.synopsis || ""}
            onChange={(e) => setForm({ ...form, synopsis: e.target.value })}
          />
        </p>
        <div className="row">
          <div style={{ flex: 1 }}>
            <label>Section</label>
            <select
              value={form.section || ""}
              onChange={(e) => setForm({ ...form, section: e.target.value || null })}
            >
              <option value="">(none — required before publish)</option>
              {(ref.data?.sections || []).map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label>Status</label>
            <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="draft">draft</option>
              <option value="published">published</option>
            </select>
          </div>
        </div>
        <p>
          <label>Categories (comma-separated)</label>
          <input
            value={(form.categories || []).join(", ")}
            onChange={(e) =>
              setForm({
                ...form,
                categories: e.target.value
                  .split(",")
                  .map((x) => x.trim())
                  .filter(Boolean),
              })
            }
          />
        </p>
        <button className="btn" onClick={save}>
          Save
        </button>
      </div>

      {!isNew && showQ.data && (
        <>
          <h2>Artwork</h2>
          <p className="muted">All three sizes are checked on the server. Wrong ratio or oversized files are rejected with a reason you can act on.</p>
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
          <Episodes showId={showQ.data.id} />
        </>
      )}
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

  return (
    <>
      <h2>Episodes</h2>
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="row">
          <div style={{ flex: 2 }}>
            <label>Search episodes</label>
            <input value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <div>
            <label>Language</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="">All</option>
              <option value="en">en</option>
              <option value="hi">hi</option>
            </select>
          </div>
          <div>
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
      {eps.data?.map((ep) => (
        <EpisodeRow key={ep.id} ep={ep} showId={showId} />
      ))}
      <h3>Add episode</h3>
      {create.isError && <ErrorBox error={create.error} />}
      <div className="card">
        <div className="row">
          <div style={{ flex: 2 }}>
            <label>Title</label>
            <input value={draft.title || ""} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
          </div>
          <div>
            <label>Season</label>
            <input
              type="number"
              value={draft.season_number}
              onChange={(e) => setDraft({ ...draft, season_number: Number(e.target.value) })}
            />
          </div>
          <div>
            <label>Episode #</label>
            <input
              type="number"
              value={draft.episode_number}
              onChange={(e) => setDraft({ ...draft, episode_number: Number(e.target.value) })}
            />
          </div>
          <div>
            <label>Language</label>
            <select value={draft.language} onChange={(e) => setDraft({ ...draft, language: e.target.value })}>
              <option value="en">en</option>
              <option value="hi">hi</option>
            </select>
          </div>
          <div>
            <label>Duration (sec)</label>
            <input
              type="number"
              value={draft.duration_seconds ?? ""}
              onChange={(e) => setDraft({ ...draft, duration_seconds: Number(e.target.value) })}
            />
          </div>
        </div>
        <p className="muted">Season 0 is reserved for trailers and won’t show as a normal season in the viewer.</p>
        <button className="btn" disabled={create.isPending || !draft.title} onClick={() => create.mutate()}>
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

  return (
    <div className="card" style={{ marginBottom: 10 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <strong>
            S{ep.season_number}E{ep.episode_number} · {ep.title}
          </strong>
          <div className="muted">
            {ep.language} · {ep.content_group} · {ep.duration_seconds ?? "no duration"}s ·{" "}
            <span className={`pill ${ep.status}`}>{ep.status}</span>
          </div>
        </div>
        <button className="btn secondary" onClick={() => setOpen(!open)}>
          {open ? "Close" : "Edit & artwork"}
        </button>
      </div>
      {open && (
        <>
          {err && <div className="banner error">{err}</div>}
          <div className="row" style={{ marginTop: 12 }}>
            <div style={{ flex: 2 }}>
              <label>Title</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div>
              <label>Duration</label>
              <input
                type="number"
                value={duration ?? ""}
                onChange={(e) => setDuration(Number(e.target.value))}
              />
            </div>
            <div>
              <label>Status</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="draft">draft</option>
                <option value="published">published</option>
              </select>
            </div>
          </div>
          <button
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
          <div className="slots">
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
