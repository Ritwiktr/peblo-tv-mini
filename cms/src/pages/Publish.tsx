import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { ErrorBox, Loading, StatusPill } from "../components/Layout";

export default function Publish() {
  const qc = useQueryClient();
  const me = useQuery({ queryKey: ["me"], queryFn: api.me });
  const report = useQuery({ queryKey: ["validation"], queryFn: api.validation });
  const runs = useQuery({ queryKey: ["runs"], queryFn: api.runs });
  const isAdmin = me.data?.role === "admin";
  const publish = useMutation({
    mutationFn: api.publish,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["runs"] });
      qc.invalidateQueries({ queryKey: ["validation"] });
    },
  });
  const rollback = useMutation({
    mutationFn: (id: string) => api.rollback(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runs"] }),
  });

  if (report.isLoading) return <Loading />;
  if (report.isError) return <ErrorBox error={report.error} />;
  const r = report.data!;
  const blocked = !r.can_publish;
  const preview = r.preview;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Publish catalogue</h1>
          <p className="lede">
            Writes a new catalogue file, then atomically replaces the live one. The viewer only ever
            reads that file — never these admin endpoints.
          </p>
        </div>
      </div>

      <div className={`card status-hero ${blocked ? "blocked" : "ready"}`}>
        <div>
          <div className="status-kicker">{blocked ? "Nothing eligible" : r.clean ? "Clean" : "Eligible subset"}</div>
          <h2>
            {blocked
              ? "Nothing would go live"
              : `This run would publish ${preview?.show_count ?? 0} shows / ${preview?.episode_count ?? 0} episodes`}
          </h2>
          <p className="muted" style={{ margin: 0 }}>
            {r.hint}
          </p>
          {preview?.sections?.length ? (
            <p className="muted">
              {preview.sections.map((s) => `${s.title} (${s.show_count})`).join(" · ")}
            </p>
          ) : null}
          {!isAdmin && (
            <div className="banner warn" style={{ marginBottom: 0 }}>
              You’re signed in as an editor. An admin has to press Publish — the API will reject it otherwise.
            </div>
          )}
          {publish.isSuccess && (
            <div className="banner ok" style={{ marginBottom: 0 }}>
              Published {publish.data.show_count} shows / {publish.data.episode_count} grouped episodes.
            </div>
          )}
        </div>
        <button
          type="button"
          className="btn accent"
          disabled={blocked || !isAdmin || publish.isPending}
          title={!isAdmin ? "Only admins can publish" : blocked ? r.hint : "Publish now"}
          onClick={() => publish.mutate()}
        >
          {publish.isPending ? "Publishing…" : r.clean ? "Publish" : "Publish eligible"}
        </button>
      </div>
      {publish.isError && <ErrorBox error={publish.error} />}

      <h2>Won’t go out in this run</h2>
      <p className="muted">
        These stay in the CMS. Publish still writes the eligible subset — it does not wait for a perfectly clean library.
      </p>
      {r.by_show.length === 0 && <p className="muted">Nothing omitted.</p>}
      {r.by_show.map((s) => (
        <div className="card issue-card" key={s.show_id}>
          <Link to={`/shows/${s.show_id}`}>{s.title} →</Link>
          {s.issues.map((i, idx) => (
            <div className="issue" key={idx}>
              {i.message}
            </div>
          ))}
        </div>
      ))}

      {(r.ingest_warnings || []).length > 0 && (
        <>
          <h2>Imported with warnings</h2>
          {r.ingest_warnings!.map((w, i) => (
            <div className="banner warn" key={i}>
              {w.message}
            </div>
          ))}
        </>
      )}

      <h2>Run history</h2>
      {runs.isLoading && <Loading />}
      {runs.data?.length === 0 && <p className="muted">No publishes yet.</p>}
      {runs.data?.map((run) => (
        <div className="card run" key={run.id}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <StatusPill status={run.status} />{" "}
              <strong>
                {run.show_count} shows · {run.episode_count} episodes
              </strong>
              <div className="muted" style={{ marginTop: 6 }}>
                {run.triggered_by || "system"} · {new Date(run.started_at).toLocaleString()}
                {run.warnings?.length ? ` · ${run.warnings.length} warning(s)` : ""}
              </div>
              {run.warnings?.length ? (
                <ul className="muted" style={{ margin: "8px 0 0", paddingLeft: 18 }}>
                  {run.warnings.slice(0, 4).map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                  {run.warnings.length > 4 && <li>+{run.warnings.length - 4} more</li>}
                </ul>
              ) : null}
              {run.error_message && <div className="banner error">{run.error_message}</div>}
            </div>
            {run.status === "success" && isAdmin && (
              <button type="button" className="btn secondary" onClick={() => rollback.mutate(run.id)}>
                Roll back to this
              </button>
            )}
          </div>
        </div>
      ))}
      {rollback.isError && <ErrorBox error={rollback.error} />}
    </>
  );
}
