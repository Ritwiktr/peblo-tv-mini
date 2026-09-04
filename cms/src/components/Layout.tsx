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
  const initial = (email[0] || "P").toUpperCase();
  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark">PEBLO</span>
          <span className="brand-sub">CMS</span>
        </Link>
        <nav className="nav">
          <NavLink to="/" end>
            Shows
          </NavLink>
          <NavLink to="/publish">Publish</NavLink>
          <div className="nav-right">
            <div className="user-chip">
              <span className="avatar">{initial}</span>
              <div className="who">
                {email}
                <span>{role}</span>
              </div>
            </div>
            <button
              type="button"
              className="btn ghost"
              onClick={() => {
                setToken(null);
                nav("/login");
              }}
            >
              Sign out
            </button>
          </div>
        </nav>
      </header>
      <main className="page">{children}</main>
    </>
  );
}

export function Loading() {
  return (
    <div>
      <div className="skeleton" />
      <div className="skeleton" />
      <div className="skeleton" />
    </div>
  );
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

export function StatusPill({ status }: { status: string }) {
  return <span className={`pill ${status}`}>{status}</span>;
}
