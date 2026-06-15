# Re-scraping app data (series, print limits, printed counts)

The tracker has **two data halves** that update at different speeds:

| Half | Lives in | Updates |
|------|----------|---------|
| **File status** (`pending`/`inprogress`/`complete`) | `data.json` | **Automatic** — `sync.py` scans Dropbox every 6h (GitHub Action) |
| **App data** (`series`, `printLimit`, `printedAuto`, `appDesign`) | the `DESIGNS` array in `index.html` | **Manual** — a browser scrape of the printing app (this doc) |

`app.perceptionexp.com` has **no API**, auto-logs-out ~hourly, and a static site can't reach a logged-in cross-origin app — so the app half can't auto-refresh. The header badge **"🗃 App data · captured \<date\>"** shows how stale it is.

## How to trigger it

There is no in-app button (there can't be). The trigger is a **Claude session**:

1. Open **Chrome** with the **Claude-in-Chrome extension** connected.
2. **Log into `app.perceptionexp.com`** (do it right before — ~hourly logout).
3. Say: **"re-scrape the app data."**

## The scrape is THREE pages (one is not enough)

`series` lives on card *instances*, but `printLimit` lives on the *design* — so you must read both, plus the series master list. Each page is a DataTables grid; load all rows first by setting **Show entries** to a large number or running
`jQuery('table.dataTable').DataTable().page.len(1000).draw()`.

### 1. `/Admin/CardSeries` — authoritative series list
Columns: **NAME**, DESCRIPTION, STATUS, CREATED.
- Pull **NAME** (canonical series spelling) and optionally **DESCRIPTION** (nice for the Releases view).
- Validate that every tracker `series` value matches a NAME here; **flag** mismatches (don't auto-rename).
- **CREATED is when the series was *made*, not a release date** — the app does not store release dates.

### 2. `/Admin/CardDesigns` — design-level attributes  ← closes the `printLimit` gap
Uncheck **"Hide inactive"** to see everything. Columns: **NAME**, SUBJECT, **DESIGN #**, DESIGNER, **ARTIST**, **LIMITED EDITION**, STATUS, CREATED.
Pull per design:
- **NAME** → the join key (matches Cards "CARD DESIGN" and the tracker's `appDesign`).
- **LIMITED EDITION "Limited (N)"** → **`printLimit` = N** (unlimited / blank → `null`).
- **DESIGN #** → stable numeric id. *Recommended: store as a new `appDesignNum` field for a rename-proof join (names have known mismatches).*
- **ARTIST** → confirms artist-card attribution (e.g. Jared Emerson); **SUBJECT** → cross-check the tracker `subject`.
- DESIGNER / STATUS / CREATED → metadata, not tracker fields today.

### 3. `/Admin/Cards` — per-instance data → `series` + `printedAuto`
Columns: SERIAL NUMBER, **CARD DESIGN**, **SERIES**, LIMITED ED #, **ACTIVE**, REDEEMED, OWNER NAME, OWNER EMAIL.
**Ignore SERIAL NUMBER, OWNER NAME, OWNER EMAIL, REDEEMED — PII.**
Group rows by **CARD DESIGN** (name) and pull:
- **SERIES** → the design's `series`. In practice one per design; if a design's cards span >1 series, **flag it** (don't pick one).
- **`printedAuto` = count of rows where ACTIVE = "Active"**. (Active ⇔ obfuscated serial `****-****-****` = the card is printed/live; Inactive = created but not yet printed.) Verified against current data: Betty 1 Active → printed 1; Chrome 2/2; Stained Glass 1 of 3 → "Printing 1/3".

## Merge & write
1. From **Card Designs**, build `name → { printLimit, designNum, artist, subject }`.
2. From **Cards**, group by design name → `{ series, printedAuto = #Active }`.
3. Join on **NAME** → the tracker's `appDesign`. Update `printLimit`, `series`, `printedAuto` in `DESIGNS` (`index.html`).
4. App designs with **no tracker match** = new designs → surface them for review (don't silently add). Tracker designs with `appDesign: null` = not in the app yet → skip.
5. **Bump `APP_DATA_CAPTURED`** in `index.html` to today's date (drives the freshness badge).
6. Show the diff for review. **Nothing is committed or pushed without approval.** Upstream data errors get *flagged*, not patched (the scrape would overwrite local edits).

## Not scraped (yet)
- **`signature`** — not surfaced in the app on table pages yet (buried in the edit view). Deferred.
- **`thumb`** — arrives with the app's next release; field + column already in place.
- **`parallel` / `variant` / `artwork`** — tracker-owned, intentionally not in the app.
- **Release dates** — app doesn't store them. If wanted, add a manual per-series release-date field in the tracker and surface it in the Releases view.

See `CLAUDE.md` for the full data model and the file-vs-app distinction.
