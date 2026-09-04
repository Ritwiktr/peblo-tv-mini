# Peblo TV Mini

CMS upload → FastAPI/Postgres → published `catalogue.json` → Netflix-style viewer.

```
CMS (React) ──► API (FastAPI + Postgres) ──► publish job ──► catalogue.json
                                                              │
Viewer (React) ◄──────────────────────────────────────────────┘
```

We grade judgment and operability. This repo is the full loop, with the seed data’s imperfections left visible for editors to fix.

## How to run

```bash
docker compose up --build
```

| Surface | URL |
|---|---|
| Viewer | http://localhost:8080 |
| CMS | http://localhost:8081 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/health |
| Docs | http://localhost:8000/docs |

Demo logins (CMS):

- **Admin** (can publish): `admin@peblo.local` / `peblo-admin`
- **Editor** (CRUD only): `editor@peblo.local` / `peblo-editor`

On first boot the API seeds 8 shows / 95 episode rows, generates placeholder artwork from `artwork_available`, and publishes whatever is eligible so the viewer isn’t empty. Remaining data-quality issues stay on **CMS → Publish**.

Sample images for upload tests live in [`data/assets/`](data/assets/) (`poster_good.jpg`, `banner_good.jpg`, `thumb_good.jpg`, plus `poster_wrong_ratio.jpg`, `thumb_tiny.jpg`, `banner_too_big.png`).

Dev without Docker: Postgres on `:5432`, `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`, then `npm install && npm run dev` in `cms/` and `viewer/`. Point `VITE_API_URL` at the API. Copy `.env.example` to `.env`.

## What the seed actually contains (the “imperfect” bits)

The validation report is meant to surface these — I did not silently “fix” them in seed:

| Issue | Where |
|---|---|
| Duplicate `(content_group, language)` | `ep_9001` is a second Hindi row for `motis-many-lives-s01e02` (already held by `ep_0004`), with a different title (“The Lost Kite (v2)”). |
| Published, no artwork | `ep_0036` *The Midnight Market* |
| Trailers only have a thumbnail | `ep_0093`, `ep_0094` (season 0) — expected, but a published *show* still needs poster/banner/thumbnail |
| Show with no section, all draft | **Rhyme Rangers** |
| Mix of draft + published | **Number Nest** |
| Copy-pasted episode titles across shows | Episode 1 is “The Lost Kite” on every series; similar reuse of “Rain on the Roof”, etc. Surfaced as an info warning. |

A unique DB constraint on `(content_group, language)` would have dropped `ep_9001` on ingest and hidden the bug from editors. Uniqueness is enforced on **writes** (409) and on **publish** (drop extras, warn). Seed imports the duplicate so it shows up in the report.

## Decisions

**Schema.** `shows → seasons → episodes`, artwork polymorphic on show *or* episode, `publish_runs` for history. Indexes: `shows(section,status)` for CMS lists, `episodes(content_group, language)` for grouping/409, `publish_runs.started_at` for run history (`002` migration), `shows.slug` unique. JSON `categories` because the list is small and filter-shaped, not join-shaped.

**Season 0.** Stored as a real season (the CMS should still be able to edit trailers). The catalogue builder attaches it as `trailer` and never as a season row.

**content_group.** Catalogue entries are one-per-group with `languages: ["en","hi"]` and a `variants` list so the viewer can switch audio without a second card.

**Artwork.** Server-side only that matters. Aspect within 4%, size within 12% of the `reference.json` targets, 200 KB ceiling. Errors are written for an editor (“This poster is 900×600… please upload 2:3 around 600×900”), not for a stack trace. Storage is a `StorageBackend` (`put` / `get` / `url` / `atomic_put_json`). Local disk is the default; `STORAGE_BACKEND=r2` plus the `R2_*` vars swaps in Cloudflare R2. Call sites do not change.

**Auth.** JWT Bearer. `editor` = CRUD. `admin` = CRUD + publish + rollback. Enforced in FastAPI dependencies, not the UI.

**Artwork surfaces (viewer).** Banner on the hero/billboard, poster (2:3) on rails and search grid, thumbnail on episode rows. Rails are the catalogue sections plus an “Available in Hindi” filter derived from published language variants — we do not duplicate titles to fake a Netflix-length row.

**Schema on boot.** Postgres runs `alembic upgrade head`. SQLite tests use `create_all` because the migration is JSONB/Postgres-only. If an existing volume was created with `create_all` (no `alembic_version` row), we `stamp` head instead of recreating tables.

**Publish gate.** The job always writes the *eligible* subset (published + section + duration + artwork, languages collapsed). The CMS dry-run shows the counts that would go live. Rows with issues are listed as omitted, not as a padlock on the button. First boot uses that same job so the viewer isn’t empty while editors still see the seed problems.

## Part E — written

### 1. Atomic publish / crash mid-run

We never overwrite the live file in place. Flow:

1. Insert `publish_runs` as `running`.
2. Build the JSON in memory.
3. Write `catalogues/catalogue-{run_id}.json` (versioned, complete).
4. If the catalogue *body* (everything except `published_at`) matches the live file, we skip the live replace — the run is still recorded. That’s the idempotent path.
5. Otherwise write a sibling `.tmp` and `os.replace` it onto `catalogues/catalogue.json`. POSIX `rename` on the same filesystem is atomic — a reader never sees a half-written document.
6. Mark the run `success` (or `failed` with the error).

If the process dies at 2–3: live file unchanged, run stuck in `running` (alert on that; see below). If it dies between 3 and 4: versioned file exists, live unchanged; republish or rollback. If it dies after 4 before 5: live catalogue is already the new complete file; the run row looks stale until the next successful publish. R2 has no cross-key rename, so we PUT the version object then PUT the live key; each GET still sees a complete object.

Rollback is a stretch we kept: restore any successful run’s versioned file through the same atomic replace.

### 2. Local disk → Cloudflare R2

Set `STORAGE_BACKEND=r2`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_BASE_URL`. That’s it — `R2Storage` speaks the S3 API. Artwork URLs then come from the R2 public base instead of `/media/...`. No router changes.

### 3. Search

`GET /catalog/search` filters the **published file** in process (title, episode title, category; `q` + `category` + `language` + `section` AND together). Facet lists come from `GET /catalog/meta`. A title page is `GET /catalog/shows/{slug}` — the viewer never calls `/admin/*` and does not walk the whole catalogue in the browser to open a show.

At this size (~8 shows) it’s noise. It stays fine into the low tens of thousands of grouped episodes on a 512 MB function. After that: don’t parse the whole file per request — keep the published document in memory (or Redis), and/or add Postgres FTS / a search engine on publish. Next step I’d take in production: load the live catalogue once, refresh on successful publish, optionally push into OpenSearch if we need typos and ranking.

### 4. Why a pre-published file

The viewer is a hot, read-mostly, child-facing surface. A static document means the browse path doesn’t join shows/seasons/episodes/artwork on every request, doesn’t depend on CMS writes, and can sit on a CDN. Publish becomes the quality gate (no draft, no missing art, language collapse).

Where it bites: **freshness**. An editor’s save is invisible until publish. That’s the point for Peblo TV (you don’t want a half-tagged episode on a living-room TV), but it is wrong for an admin preview. Also: search/filter flexibility is bounded by what you baked into the file. We didn’t put playback URLs or progress in it.

### 5. Left out, and AI

Left out on purpose: a real video player, transcoding, per-episode playback tokens, SSO, i18n of the CMS chrome, an append-only audit log of field-level edits. Continue Watching is omitted rather than faked — there’s no playback progress in this take-home.

AI: **Cursor Grok 4.6** wrote most of this repo. I accepted the overall shape (three processes, storage ABC, atomic replace, seed-visible duplicates). I rejected a unique DB constraint that would have swallowed `ep_9001`, client-side-only image checks, and searching the catalogue in the viewer.

## Alerting

`GET /health` checks Postgres and whether a live catalogue exists.

**Alert on: publish run stuck in `running` for > 2 minutes, or a spike in 5xx on `POST /admin/catalog/publish`.** A hung publish means either the process died after inserting the run (live catalogue stale or fine — check the versioned object) or storage is wedged. That’s the one failure that silently stops new content reaching kids. Catalogue-missing on a *running* viewer environment is the second-page alert; first boot before publish is expected.

## Secrets in production

`.env.example` lists every variable. In production I would **not** bake secrets into the image or compose file. Put `JWT_SECRET`, DB password, and R2 keys in the platform secret store (GitHub OIDC → cloud secret manager, or Fly/Render/K8s secrets). Rotate JWT_SECRET by dual-accepting old+new for one TTL. Demo passwords in this repo are for local compose only.

## CI

`.github/workflows/ci.yml`: ruff + pytest (Postgres service + Alembic on CI), frontend typecheck/build, `docker compose up` until `/health` + viewer + CMS respond. The **deploy** job is written and explained; it does not push to a real registry.

## Time (approx.)

- Backend (schema, artwork, publish, search, auth, seed, tests): ~3.5h
- CMS: ~2h
- Viewer: ~1.5h
- Compose / CI / README: ~1h

## Tests

```bash
cd backend && pytest -q
```

Risky bits covered: artwork aspect/size/KB (including HTTP 422 on poster, banner, and thumbnail), language grouping on publish, idempotent re-publish, filter composition, atomic replace, role enforcement, duplicate `(content_group, language)` on write, catalogue slug + meta endpoints.
