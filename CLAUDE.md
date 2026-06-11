# Perception Cards – Design Tracker

## What this is
A single-page web app for tracking the design/production status of custom trading cards. Hosted on GitHub Pages. All persistent data lives in `data.json` in this repo. No backend, no build step.

**Live app:** https://ddpedersen.github.io/perception-cards-tracker/
**Repo:** https://github.com/ddpedersen/perception-cards-tracker

---

## Files

| File | Purpose |
|------|---------|
| `Card Tracker.html` | The entire app — HTML, CSS, and JS in one file |
| `data.json` | Card status/notes/print data, written by sync and by the app's Save button |
| `sync.py` | Python script that scans Dropbox and upgrades card statuses |
| `.github/workflows/sync-dropbox.yml` | Runs `sync.py` every 6 hours via GitHub Actions |

---

## Architecture

### App (`Card Tracker.html`)
- **No build step.** Pure HTML/CSS/JS. Edit the file and push — GitHub Pages serves it.
- Card definitions are **hardcoded** in the `CATEGORIES` array inside the JS. Each card has: `id`, `name`, `ai`/`front`/`back` booleans, `flags[]`, `appDesign`, `printLimit`, `printedAuto`.
- **Runtime data** (status, notes, printed count) loads from `data.json` via the GitHub Contents API using a PAT stored in localStorage.
- Save writes back to `data.json` via the same API.
- The PAT is entered once by the user and saved to their browser's localStorage.

### Data (`data.json`)
Schema per card entry:
```json
{
  "card-id": {
    "status": "pending | inprogress | complete | onhold | archived",
    "notes": "string",
    "printed": null
  }
}
```
- `status` is the only field the sync script writes. `notes` and `printed` are user-managed.
- Every card entry **must** have a `status` field — missing status crashes the renderer.

### Status rules
| Status | Meaning | Source |
|--------|---------|--------|
| `pending` | No files found | sync default |
| `inprogress` | `.ai` file found, no PDF | sync auto |
| `complete` | `.pdf` file found | sync auto |
| `onhold` | Project paused | manual only |
| `archived` | Done/shelved | manual only |

Statuses **only upgrade** (pending→inprogress→complete). `onhold` and `archived` are never touched by the sync.

### Sync (`sync.py`)
- Runs in GitHub Actions (every 6h + manual dispatch).
- Uses Dropbox API v2 with **root namespace** `2434352035` — required for Dropbox Business team folders. All `list_folder` calls include header `Dropbox-API-Path-Root: {".tag":"namespace_id","namespace_id":"2434352035"}`.
- Scans each card's folder path under `/Perception Cards/Projects/` for `.ai` or `.pdf` files (non-recursive).
- Card ID → folder path mapping is in the `CARD_PATHS` dict in `sync.py`. Must stay in sync with card `id` values in the HTML.
- Uses only Python stdlib (no pip needed in CI).
- Commits updated `data.json` back to the repo via the GitHub Contents API using the `GH_PAT` secret.

### GitHub Actions secrets
- `DROPBOX_REFRESH_TOKEN`
- `DROPBOX_APP_KEY`
- `DROPBOX_APP_SECRET`
- `GH_PAT` — fine-grained PAT with Contents: read/write on this repo

---

## Key constraints

⚠️ **Do not use the app's own edit UI (status dropdown, notes textarea) to modify card data during development.** Edit `data.json` directly. The edit UI is for the end user; using it during dev creates race conditions with the sync.

⚠️ **Do not downgrade statuses.** The sync and `upgrade_status()` function enforce this. Any manual patch to `data.json` should respect the same rule.

---

## Current state (as of June 2026)

- **67 cards** defined in the HTML
- **data.json** has all 67 entries with valid statuses: ~59 complete, 4 inprogress, 4 pending
- Sync pipeline is fully operational
- App loads cleanly, no JS errors

### Known technical debt
- `Card Tracker.html` uses `btoa(unescape(encodeURIComponent(...)))` for save and `decodeURIComponent(escape(atob(...)))` for load. Works for pure-ASCII JSON but fragile — replace with `TextEncoder`/`TextDecoder` if non-ASCII data is ever stored.
- Card definitions (in HTML) and folder paths (in `sync.py`) are maintained separately and must be kept in sync manually.

---

## Local dev workflow

```bash
# No build step needed. Edit Card Tracker.html and open in browser.
# GitHub API features (load/save) require the live Pages URL or a local server + valid PAT.

# Push to deploy (Pages updates in ~30 seconds)
git add "Card Tracker.html" data.json sync.py
git commit -m "your message"
git push
```

To test sync locally:
```bash
DROPBOX_REFRESH_TOKEN=... DROPBOX_APP_KEY=... DROPBOX_APP_SECRET=... GH_PAT=... python sync.py
```

---

## Card data structure (HTML)

Each card object in `CATEGORIES[].cards[]`:
```js
{
  id: 'kobe-legendary',        // matches data.json key AND sync.py CARD_PATHS key
  name: 'Kobe Legendary (base)',
  ai: true,                    // .ai source file exists
  front: true,                 // Front PDF exists
  back: true,                  // Back PDF exists
  flags: ['warning text'],     // issues shown on card
  appDesign: 'Kobe Legendary', // name in printing app, or null
  printLimit: 1,               // production print limit, or null
  printedAuto: 1,              // count auto-pulled from printing app
  appNameNote: 'optional note about name mismatch'
}
```

STATUS config (JS) — every `data.json` status value must be a key here:
```js
const STATUS = {
  pending:    { label: 'Pending',     badge: 'badge-pending'    },
  inprogress: { label: 'In Progress', badge: 'badge-inprogress' },
  complete:   { label: 'Complete',    badge: 'badge-complete'   },
  onhold:     { label: 'On Hold',     badge: 'badge-onhold'     },
  archived:   { label: 'Archived',    badge: 'badge-archived'   },
};
```
