import { useState } from "react";
import type { Art } from "../api/client";

const LABELS: Record<string, string> = {
  poster: "2:3 · ~600×900 · max 200 KB. Browse rows.",
  banner: "16:9 · ~1280×720 · max 200 KB. Hero / billboard.",
  thumbnail: "16:9 · ~640×360 · max 200 KB. Episode lists.",
};

export function ArtworkSlot({
  kind,
  current,
  onUpload,
}: {
  kind: string;
  current?: Art;
  onUpload: (file: File) => Promise<void>;
}) {
  const [preview, setPreview] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const src = preview || current?.url;

  async function handle(file: File) {
    setErr(null);
    setPreview(URL.createObjectURL(file));
    setBusy(true);
    try {
      await onUpload(file);
    } catch (ex) {
      setErr((ex as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className={`slot ${drag ? "drag" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        const file = e.dataTransfer.files?.[0];
        if (file) void handle(file);
      }}
    >
      <header>
        <strong>{kind}</strong>
        {current ? <span className="pill published">uploaded</span> : <span className="pill draft">missing</span>}
      </header>
      <p className="muted" style={{ margin: "0 0 8px" }}>
        {LABELS[kind]}
      </p>
      <div className={`frame ${kind}`}>
        {src ? <img src={src} alt={`${kind} preview`} /> : <span>Drop an image, or choose a file</span>}
      </div>
      <label className="btn secondary file-btn">
        {busy ? "Uploading…" : src ? "Replace" : "Choose file"}
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          disabled={busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handle(file);
            e.target.value = "";
          }}
        />
      </label>
      {err && <p className="banner error">{err}</p>}
    </div>
  );
}
