import { FormEvent, useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { BellIcon, Caret, SearchIcon } from "./Icons";

export function Nav({ q = "" }: { q?: string; category?: string; language?: string }) {
  const nav = useNavigate();
  const loc = useLocation();
  const [query, setQuery] = useState(q);
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(!!q);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  function go(e: FormEvent) {
    e.preventDefault();
    const p = new URLSearchParams(loc.search);
    if (query) p.set("q", query);
    else p.delete("q");
    nav(`/search?${p}`);
  }

  return (
    <header className={`nav ${scrolled || loc.pathname !== "/" ? "scrolled" : ""}`}>
      <Link to="/" className="logo">
        PEBLO
      </Link>
      <nav className="nav-links">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          Home
        </NavLink>
        <NavLink to="/search?section=series">TV Shows</NavLink>
        <NavLink to="/search?section=songs">Movies</NavLink>
        <NavLink to="/search?section=minisodes">New & Popular</NavLink>
        <NavLink to="/search?language=hi">My List</NavLink>
        <NavLink to="/search?language=hi">Browse by Languages</NavLink>
      </nav>
      <div className="nav-right">
        {open ? (
          <form className="search-wrap" onSubmit={go}>
            <SearchIcon size={16} />
            <input
              className="search-field"
              type="search"
              autoFocus
              placeholder="Titles, people, genres"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onBlur={() => {
                if (!query) setOpen(false);
              }}
            />
          </form>
        ) : (
          <button type="button" className="icon-btn" onClick={() => setOpen(true)} aria-label="Search">
            <SearchIcon />
          </button>
        )}
        <button type="button" className="icon-btn" aria-label="Notifications">
          <BellIcon />
        </button>
        <button type="button" className="profile">
          <span className="avatar">K</span>
          <Caret />
        </button>
      </div>
    </header>
  );
}
