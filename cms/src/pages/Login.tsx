import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../api/client";

const DEMOS = [
  { label: "Admin", email: "admin@peblo.local", password: "peblo-admin" },
  { label: "Editor", email: "editor@peblo.local", password: "peblo-editor" },
];

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@peblo.local");
  const [password, setPassword] = useState("peblo-admin");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(nextEmail = email, nextPassword = password) {
    setBusy(true);
    setErr(null);
    try {
      const t = await api.login(nextEmail, nextPassword);
      setToken(t.access_token);
      nav("/");
    } catch (ex) {
      setErr((ex as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login">
      <form
        className="card"
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <div className="brand-mark">PEBLO</div>
        <p className="brand-sub" style={{ margin: "0 0 8px" }}>
          Content studio
        </p>
        <h1>Sign in</h1>
        <p className="muted">Manage shows, artwork, and the published catalogue.</p>
        {err && <div className="banner error">{err}</div>}
        <p>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="username"
          />
        </p>
        <p>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </p>
        <button className="btn accent" disabled={busy} style={{ width: "100%" }}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="muted" style={{ marginTop: 18, marginBottom: 8 }}>
          Demo accounts — admin can publish, editor cannot.
        </p>
        <div className="demo-row">
          {DEMOS.map((d) => (
            <button
              key={d.email}
              type="button"
              className="btn secondary"
              disabled={busy}
              onClick={() => {
                setEmail(d.email);
                setPassword(d.password);
                void submit(d.email, d.password);
              }}
            >
              {d.label}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
