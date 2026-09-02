import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const CATS = [
  "",
  "adventure",
  "folk",
  "friendship",
  "india",
  "language",
  "learning",
  "maths",
  "music",
  "nature",
  "reading",
  "science",
  "singalong",
  "stories",
  "travel",
  "values",
];

export function Nav({
  q = "",
  category = "",
  language = "",
}: {
  q?: string;
  category?: string;
  language?: string;
}) {
  const nav = useNavigate();
  const [query, setQuery] = useState(q);
  const [cat, setCat] = useState(category);
  const [lang, setLang] = useState(language);

  function go(e: FormEvent) {
    e.preventDefault();
    const p = new URLSearchParams();
    if (query) p.set("q", query);
    if (cat) p.set("category", cat);
    if (lang) p.set("language", lang);
    nav(`/search?${p}`);
  }

  return (
    <header className="nav">
      <Link to="/" className="logo">
        PEBLO <span>TV</span>
      </Link>
      <form className="searchbar" onSubmit={go}>
        <input
          placeholder="Search shows & episodes"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select value={cat} onChange={(e) => setCat(e.target.value)}>
          <option value="">All categories</option>
          {CATS.filter(Boolean).map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <select value={lang} onChange={(e) => setLang(e.target.value)}>
          <option value="">All languages</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
        </select>
        <button type="submit" style={{ background: "var(--gold)", color: "#111", border: 0, borderRadius: 999, padding: "8px 14px", cursor: "pointer" }}>
          Search
        </button>
      </form>
    </header>
  );
}
