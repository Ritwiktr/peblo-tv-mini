import { useState } from "react";
import type { Art } from "../api/client";

const LABELS: Record<string, string> = {
  poster: "Poster — 2:3, around 600×900, max 200 KB. Used on browse rows.",
  banner: "Banner — 16:9, around 1280×720, max 200 KB. Used on the hero.",
  thumbnail: "Thumbnail — 16:9, around 640×360, max 200 KB. Used on episode lists.",
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

  return (
    <div className="slot">
      <strong style={{ textTransform: "capitalize" }}>{kind}</strong>
      <p className="muted">{LABELS[kind]}</p>
      {(preview || current?.url) && (
        <img src={preview || current!.url} alt={`${kind} preview`} style={{ margin: "8px 0" }} />
      )}
      <input
        type="file"
        accept="image/jpeg,image/png,image/webp"
        disabled={busy}
        onChange={async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
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
        }}
      />
      {busy && <p className="muted">Uploading…</p>}
      {err && <p className="banner error">{err}</p>}
    </div>
  );
}
