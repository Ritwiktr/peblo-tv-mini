import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../api/client";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@peblo.local");
  const [password, setPassword] = useState("peblo-admin");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  return (
    <div className="login">
      <form
        className="card"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setErr(null);
          try {
            const t = await api.login(email, password);
            setToken(t.access_token);
            nav("/");
          } catch (ex) {
            setErr((ex as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <h1>Peblo CMS</h1>
        <p className="muted">Sign in to manage shows, artwork, and publishing.</p>
        {err && <div className="banner error">{err}</div>}
        <p>
          <label>Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
        </p>
        <p>
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </p>
        <button className="btn" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="muted" style={{ marginTop: 16 }}>
          Demo accounts: admin@peblo.local / peblo-admin (can publish) and
          editor@peblo.local / peblo-editor (cannot publish).
        </p>
      </form>
    </div>
  );
}
