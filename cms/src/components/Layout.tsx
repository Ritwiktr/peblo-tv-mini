import type { ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { setToken } from "../api/client";

export function Layout({
  children,
  email,
  role,
}: {
  children: ReactNode;
  email: string;
  role: string;
}) {
  const nav = useNavigate();
  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand" style={{ textDecoration: "none" }}>
          Peblo <span>CMS</span>
        </Link>
        <nav className="nav">
          <NavLink to="/" end>
            Shows
          </NavLink>
          <NavLink to="/publish">Publish</NavLink>
          <span className="muted">
            {email} · {role}
          </span>
          <button
            className="btn secondary"
            onClick={() => {
              setToken(null);
              nav("/login");
            }}
          >
            Sign out
          </button>
        </nav>
      </header>
      <main className="page">{children}</main>
    </>
  );
}

export function Loading() {
  return <p className="muted">Loading…</p>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="banner empty">{children}</div>;
}

export function ErrorBox({ error }: { error: unknown }) {
  const err = error as { status?: number; message?: string };
  if (err.status === 403) {
    return (
      <div className="banner error">
        You don’t have permission to do that. Sign in as an admin, or ask one to help.
      </div>
    );
  }
  if (err.status === 401) {
    return <div className="banner error">Please sign in again.</div>;
  }
  return <div className="banner error">{err.message || "Something went wrong."}</div>;
}
