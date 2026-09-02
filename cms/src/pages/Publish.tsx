import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { ErrorBox, Loading } from "../components/Layout";

export default function Publish() {
  const qc = useQueryClient();
  const report = useQuery({ queryKey: ["validation"], queryFn: api.validation });
  const runs = useQuery({ queryKey: ["runs"], queryFn: api.runs });
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

  return (
    <>
      <h1>Publish catalogue</h1>
      <p className="muted">
        Publishing writes a new catalogue file, then atomically replaces the live one. The viewer only
        ever reads that file — never these admin endpoints.
      </p>
      <div className="card">
        <p>{r.hint}</p>
        {blocked && (
          <div className="banner warn">
            Publish is disabled until the blocking items below are fixed.
          </div>
        )}
        <button
          className="btn"
          disabled={blocked || publish.isPending}
          title={blocked ? r.hint : "Publish now"}
          onClick={() => publish.mutate()}
        >
          {publish.isPending ? "Publishing…" : "Publish"}
        </button>
        {publish.isError && <ErrorBox error={publish.error} />}
        {publish.isSuccess && (
          <p className="muted">
            Published {publish.data.show_count} shows / {publish.data.episode_count} grouped episodes.
          </p>
        )}
      </div>

      <h2>Blocking</h2>
      {r.blocking.length === 0 && <p className="muted">Nothing blocking.</p>}
      {r.by_show.map((s) => (
        <div className="card" key={s.show_id} style={{ marginBottom: 10 }}>
          <strong>{s.title}</strong>
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
        <div className="card" key={run.id} style={{ marginBottom: 8 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <span className={`pill ${run.status === "success" ? "published" : "draft"}`}>{run.status}</span>{" "}
              {run.show_count} shows · {run.episode_count} episodes · {run.triggered_by || "system"} ·{" "}
              {new Date(run.started_at).toLocaleString()}
              {run.warnings?.length ? (
                <div className="muted">{run.warnings.length} warning(s) during this run</div>
              ) : null}
              {run.error_message && <div className="banner error">{run.error_message}</div>}
            </div>
            {run.status === "success" && (
              <button className="btn secondary" onClick={() => rollback.mutate(run.id)}>
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
