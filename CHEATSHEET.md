# Perception Cards — Naming Cheat Sheet

Quick card. The full spec is [`NAMING.md`](NAMING.md).

## The formula (one string names the folder, the files, and the app design)

```
<Anchor> - <Parallel> - <Variant> - <Tier> - <Product>
```

Separator is **space-hyphen-space** ` - `. **Drop** any part that doesn't apply; **never reorder**.

## Segments

| Part | When | What |
|---|---|---|
| **Anchor** | always | Painting title for artist cards (`MJ in Flight`, `Black Mamba Portrait`, `NeoLeo`); the subject for everything else (`Kerry Wood`). |
| **Parallel** | if it has one | Must already exist in the Vocabulary. A true one-off can use a plain word (`Gum Card`). |
| **Variant** | only with a parallel | The sub-treatment (`Gold`, `Rare Air`). **Omit for the parallel's base card.** |
| **Tier** | limited runs only | `1of1`, `of2`, `of10`. Omit if unlimited. |
| **Product** | derivatives only | `Plate`, `Box`. |

## Files inside the design's folder

```
<full name>.ai            ← exactly one, neutral name (never "Front.ai")
<full name> - Front.pdf
<full name> - Back.pdf
```

- **Folder** = the full design name (or the **painting name** if you keep variants together in one folder).
- **App design name** = the same string *ideally* — but a legacy name is OK: the tracker fuzzy-matches and you confirm the link.

## Hard don'ts

- No ` - ` **inside** a value → `Angel Rare Air` ✓, `Angel - Rare Air` ✗
- No slashes → `1of1`, not `1/1`. Plain hyphens, not en-dashes (–).
- No `final` / `v2` / year / `new` in names (version inside the .ai, archive old exports).
- **Don't invent** a parallel/variant that isn't in the Vocabulary — add it in the **🏷 Vocabulary** tab first, *then* name the file.

## The loop

1. Create file → named to the key → appears in **🆕 Discovered** (Dashboard).
2. New parallel/variant? → add it in **🏷 Vocabulary** → Save.
3. **+ Add to designs** to promote it into the tracked list.
4. Once it's in the printing app → scrape → **🔗 Link** the app design to it (fills series/printed, no duplicate).

## Current vocabulary

- **Legendary**: Angel · Gold · Scoreboard · Silver Holo
- **Holographic**: Chrome · Satin · Snake · Gold · Gold Matrix
- **Angel**: *(base)* · Clear Air · Rare Air · Halo
- **Clear**: Glass
- **Leather**: GOAT
- **Snake Skin · Stained Glass · Space**: parallel-only (no variants)

*(The Vocabulary tab in the app is the live source — this list is a snapshot as of 2026-06-17.)*

## Examples

- `Black Mamba Portrait - Holographic - Chrome - of2`
- `MJ in Flight - Angel - Rare Air - of10`
- `MJ in Flight - Leather - GOAT - 1of1`
- `NeoLeo - Holographic - Gold Matrix - 1of1`
- `Kerry Wood - Gum Card - of3`
- `Black Mamba Portrait - Snake Skin - 1of1 - Box` *(derivative)*
