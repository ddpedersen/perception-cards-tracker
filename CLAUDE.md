# Perception Cards – Design Tracker

## What this is
A single-page web app for tracking the design/production status of custom trading cards, plus release-planning rollups. Hosted on GitHub Pages. All persistent data lives in `data.json` in this repo. No backend, no build step.

**Live app:** https://ddpedersen.github.io/perception-cards-tracker/
**Repo:** https://github.com/ddpedersen/perception-cards-tracker

---

## Files

| File | Purpose |
|------|---------|
| `index.html` | The entire app — HTML, CSS, and JS in one file |
| `data.json` | Runtime status/notes/printed data, keyed by design id. Written by sync and by the app's Save button |
| `sync.py` | Python script that scans Dropbox and upgrades design statuses |
| `.github/workflows/sync-dropbox.yml` | Runs `sync.py` every 6 hours via GitHub Actions |
| `.claude/launch.json` + `.claude/static-server.js` | Local preview server (Node, no deps) on port 8753 — dev only |

> ⚠️ The app file is **`index.html`**. (Earlier docs called it "Card Tracker.html" — that name is wrong.)

---

## Architecture

### App (`index.html`)
- **No build step.** Pure HTML/CSS/JS. Edit the file and push — GitHub Pages serves it.
- Design definitions are **hardcoded** in the flat `DESIGNS` array inside the JS (one object per design).
- **Runtime data** (status, notes, printed count) loads from `data.json` via the GitHub Contents API using a PAT stored in localStorage. Save writes back via the same API. The PAT is entered once and saved to the browser.

### Designs vs. cards (mirrors the user's web-app DB)
- **Design** = a card layout = a row in `DESIGNS`. Carries `category` (1), `subject` (1), `artwork` (0-1), `parallel` (0-1), `variant` (0-1), `series`, `signature`, `thumb`, plus file/print fields.
- **Card** = a serialized physical instance (lives in the user's app DB, **not** modeled individually here). A card has exactly **one** series; a design rolls up to one-or-more series from its cards.

### The four dimensions
| Dimension | Behaves like | Membership |
|-----------|--------------|------------|
| **Category** | hard filter | each design in exactly **one** (`CATEGORIES` config) |
| **Subject** | the athlete/person | one per design |
| **Artwork** | the source painting (artist cards only) | one per design or null; **when set, the unit completeness is measured against** |
| **Series** | the release tag | rolls up from the design's cards; empty until scraped |

**Sets (completeness unit):** artist-card designs derive from a *painting* (`artwork`), and each painting builds toward its own set — e.g. Jordan's *MJ Portrait* and *MJ in Flight* paintings are two separate sets, each with its own template. Non-artist designs keep the subject as the set. Set key = `subject + '|' + artwork` (or just `subject` when `artwork` is null); sets span categories (the Court Dreams graded plate joins the Court Dreams painting set). `artwork` is **user-maintained knowledge** (not in the printing app, not scraped) — unlike `series`/`signature`/`thumb`, it's fine to edit by hand.

**Parallels & variants:** the full hierarchy is *Subject → Painting → Parallel → Variant (→ Tier)*. A **parallel** is a treatment line that recurs across paintings/subjects/categories (e.g. Legendary — found on Kobe, LeBron, and Derek's soccer cards). A **variant** is a flat-string sub-treatment within one parallel (Legendary → Gold, Scoreboard, Angel, Silver Holo); **no sub-variants** — "Angel Rare Air" is one variant. Each parallel has its own variant list (`PARALLELS` config); a variant's `tier` is a **soft default** ("Gold is usually /3") used only for mismatch alerts. Like `artwork`, `parallel`/`variant` are user-maintained in the tracker (source of truth). **Naming alerts** (`namingAlerts(d)`, derived at render — never stored in `flags`) fire when: a variant has no parallel (file/app name skipped the parallel level — true for all 8 *MJ in Flight* designs), the parallel/variant isn't in the vocabulary, or the design's `printLimit` differs from the variant's default tier. They count toward the Issues filter via `issueCount(d)`. ⚠ "Kobe Legendary"/"LeBron Legendary" `artwork` values are **placeholders** — Legendary is the *parallel*; the actual paintings were never named (Derek will supply names, e.g. "Kobe Shirt Pull"). Planned: once the naming convention is final, the sync will parse well-named files and auto-fill parallel/variant.

### Views (header tabs)
- **Dashboard** — tiles (Designs · Subjects · **Sets Complete** · status counts), a **By-Set** completeness scorecard (one row per painting for artist cards, per subject otherwise; tier pips vs. that set's template), **By-Series** rollup (players/designs per release), **By-Category** rollup.
- **Designs** — detail table: thumb · name · subject (+🎨 painting) · parallel › variant (amber ⚠ when variant lacks a parallel) · series · signature · tier · printed · status · files · flags. Category dropdown + status filters + search (searches artwork/parallel/variant too). Row name expands flags/notes/naming alerts.
- **Grid** — the original card layout (preserved).

### Set completeness template (the "24-card set")
- `SET_TEMPLATE_DEFAULT` = `/10×1 · /5×1 · /3×1 · /2×1 · 1/1×4` → 8 designs / 24 serialized cards.
- Per-set size overrides via `SET_TEMPLATE_OVERRIDES`, **keyed by artwork title** (painting sets) or subject name (subject sets) — one painting can run a 30-card set, another a 12-card set.
- `setsIn(pool)` groups designs into sets; `setReport(set)` buckets them by `printLimit`; tiers are scored filled/missing/over. Off-template runs (e.g. `/50`) → **extras**; `printLimit: null` → **untiered**. `templateFor(set)` looks up `set.artwork || set.subject`.

### Data (`data.json`)
Schema per design entry (**unchanged** by the new fields):
```json
{
  "design-id": {
    "status": "pending | inprogress | complete | onhold | archived",
    "notes": "string",
    "printed": null
  }
}
```
- `status` is the only field the sync writes. `notes`/`printed` are user-managed.
- Every entry **must** have a `status` field — a missing status crashes the renderer. (Designs absent from `data.json`, like `matt-empty`, default to `pending` in-app.)
- `category` / `subject` / `artwork` / `parallel` / `variant` / `series` / `signature` / `thumb` live **only in `index.html`** (design-level), not in `data.json`.

### Status rules
| Status | Meaning | Source |
|--------|---------|--------|
| `pending` | No files found | sync default |
| `inprogress` | `.ai` file found, no PDF | sync auto |
| `complete` | `.pdf` file found | sync auto |
| `onhold` | Project paused | manual only |
| `archived` | Done/shelved | manual only |

Statuses **only upgrade** (pending→inprogress→complete). `onhold`/`archived` are never touched by the sync.

**Derived `printing` status (display-only):** the app's `effectiveStatus(d)` shows a limited design as **"Printing X/Y"** (blue) when its file-`status` is `complete` but it isn't fully printed (`printedAuto < printLimit`). This enforces the rule *complete = files done AND printed == limit* without touching the sync-owned `status`. `printedAuto` is the printed-card count scraped from the app's Cards table (printed = obfuscated serial, or real serial + owner). Note: `printedValue()` uses loose `!= null` because data.json entries omit the `printed` key (`undefined`) — using `!== null` makes printed fields render blank.

### Sync (`sync.py`)
- Runs in GitHub Actions (every 6h + manual dispatch).
- Dropbox API v2 with **root namespace** `2434352035` (required for the Business team folder). All `list_folder` calls send header `Dropbox-API-Path-Root: {".tag":"namespace_id","namespace_id":"2434352035"}`.
- Scans each design's folder under `/Perception Cards/Projects/` for `.ai`/`.pdf` (non-recursive).
- Design ID → folder mapping is the `CARD_PATHS` dict; must stay in sync with `id` values in `DESIGNS`.
- Stdlib only. Commits `data.json` back via the Contents API using `GH_PAT`.
- **Keys on design `id` and only writes `status`** — so the new design-level fields and the category merge did not affect it.

### GitHub Actions secrets
`DROPBOX_REFRESH_TOKEN`, `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, `GH_PAT` (fine-grained, Contents: read/write).

---

## Key constraints

⚠️ **Don't fabricate `series` / `signature` / `thumb` values.** The fields/columns exist but are intentionally empty — they'll be populated by a scrape from the user's app. Leave them null/empty until then.

⚠️ **Don't correct upstream data errors in the tracker — flag them.** If a design is mis-filed (e.g. `kobe-court-dreams` is a LeBron design in the Kobe folder), add a flag like `"Move file to correct location"` rather than silently re-attributing it. The sync re-scrapes from source and would overwrite local patches; fixing upstream is permanent.

⚠️ **Don't use the app's own edit UI to change data during development.** Edit `data.json` directly. The edit UI is for the end user; using it during dev races with the sync.

⚠️ **Don't downgrade statuses.** `sync.py`'s `upgrade_status()` enforces this; manual `data.json` patches should too.

---

## Current state (as of June 2026)

- **67 designs** defined in `index.html`, across **10 categories**; **33 subjects**; **11 painting sets** (artwork tagged on all 23 artist designs + the Court Dreams graded plate).
- `data.json` has 66 entries (the 67th, `matt-empty`, defaults to pending): **~59 complete, 4 inprogress, 3 pending**.
- **0/37 sets** currently complete (e.g. MJ in Flight 6/8; Black Mamba Portrait 4/8; Kobe Legendary 3/8). Painting names were inferred from design/folder naming — user should review/rename ("Kobe Legendary"/"LeBron Legendary" are confirmed placeholders).
- **Parallels:** vocabulary has 1 parallel (Legendary, 4 variants, no tier defaults yet). `parallel` set on 8 designs (5 Kobe Legendary + LeBron + 2 soccer); `variant` set on those + the 8 MJ in Flight designs, which alert "missing parallel" by design (50 flagged designs total incl. naming alerts). Pending from Derek: painting names, fuller parallel/variant vocabulary (+ default tiers), MJ in Flight parallel assignments, then a **naming key** doc + sync parsing.
- Sync pipeline operational; app loads cleanly, no JS errors.

### Known technical debt
- Save/load use `btoa(unescape(encodeURIComponent(...)))` / `decodeURIComponent(escape(atob(...)))`. Fine for ASCII JSON but fragile — switch to `TextEncoder`/`TextDecoder` if non-ASCII data is ever stored.
- `DESIGNS` (in HTML) and `CARD_PATHS` (in `sync.py`) are maintained separately and must be kept in sync by hand.

---

## Local dev workflow

⚠️ **Don't `git push` without Derek's explicit approval.** Pushing deploys the live site (~30s). Commit locally, demo the change on the localhost preview, and ask before pushing.

```bash
# No build step. Edit index.html and open in a browser.
# GitHub load/save needs the live Pages URL or a local server + valid PAT.

# Push to deploy (Pages updates in ~30 seconds) — ONLY after Derek approves
git add index.html data.json sync.py
git commit -m "your message"
git push
```

**Local preview (this repo):** a Node static server is configured at `.claude/static-server.js` (port 8753). The Connect-to-GitHub modal has no close button; to view with real data without entering a token, load the local `data.json` into the running page:
```js
// in the preview/devtools console:
var x=new XMLHttpRequest(); x.open('GET','/data.json',false); x.send();
appData=JSON.parse(x.responseText); hideTokenModal(); renderAll();
```
(Temporary — resets on reload. On the live site, the saved PAT loads data automatically.)

To test sync locally:
```bash
DROPBOX_REFRESH_TOKEN=... DROPBOX_APP_KEY=... DROPBOX_APP_SECRET=... GH_PAT=... python sync.py
```

---

## Design data structure (HTML)

Each object in the `DESIGNS` array:
```js
{
  id: 'kobe-legendary',          // matches data.json key AND sync.py CARD_PATHS key
  name: 'Kobe Legendary (base)',
  category: 'artist-jared',      // one of the CATEGORIES ids
  subject: 'Kobe Bryant',        // athlete/person, or null (null = in no set)
  artwork: 'Kobe Legendary',     // source painting (artist cards) — drives per-painting sets; null elsewhere. ⚠ this one's a placeholder (painting unnamed)
  parallel: 'Legendary',         // treatment line, recurs across paintings/subjects/categories; must be in PARALLELS; null = not yet assigned
  variant: 'Gold',               // sub-treatment within the parallel (flat string, no sub-variants); variant without parallel ⇒ naming alert
  series: '',                    // release; empty until scraped
  signature: null,               // 'Artist' | 'Designer' | 'Player-Subject' | null
  thumb: null,                   // image URL; null until scraped
  ai: true,                      // .ai source file exists
  front: true,                   // Front PDF exists
  back: true,                    // Back PDF exists
  flags: ['warning text'],       // issues shown on the design
  appDesign: 'Kobe Legendary',   // name in printing app, or null
  printLimit: 1,                 // serial run / tier, or null
  printedAuto: 1,                // count auto-pulled from printing app
  appNameNote: '...',            // optional: file/app name mismatch
  appAlso: ['...']               // optional: related app entries
}
```

`CATEGORIES` (JS) — top-level groups; each design's `category` must be one of these ids:
```js
const CATEGORIES = [
  { id:'artist-jared',    label:'Artist Cards – Jared Emerson' },
  { id:'artist-athletic', label:'Artist Cards – Athletic Art' },
  { id:'baseball',        label:'Baseball Designs' },
  { id:'football',        label:'Football Designs' },
  { id:'micro-wrestling', label:'Micro Wrestling' },
  { id:'graded-plates',   label:'Graded Plates' },
  { id:'magical',         label:'Magical Cards' },
  { id:'philanthropy',    label:'Philanthropic Projects' },
  { id:'derek-personal',  label:"Derek's Personal Projects" },
  { id:'matt-personal',   label:"Matt's Personal Projects" },
];
```

`STATUS` config (JS) — every `data.json` status value must be a key here:
```js
const STATUS = {
  pending:    { label: 'Pending',     badge: 'badge-pending',    color: 'var(--muted)' },
  inprogress: { label: 'In Progress', badge: 'badge-inprogress', color: 'var(--amber)' },
  complete:   { label: 'Complete',    badge: 'badge-complete',   color: 'var(--green)' },
  onhold:     { label: 'On Hold',     badge: 'badge-onhold',     color: 'var(--blue)'  },
  archived:   { label: 'Archived',    badge: 'badge-archived',   color: '#555'         },
};
```
