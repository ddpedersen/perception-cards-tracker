# Perception Cards – Naming Key

One name, everywhere. The same string names the Dropbox **folder**, the **files** inside it, and the **app design**. The tracker validates against this key, and the sync will eventually parse it to auto-fill parallel/variant.

---

## The formula

```
<Set Anchor> - <Parallel> - <Variant> - <Tier> - <Product>
```

Separator is exactly **space-hyphen-space** (` - `). Drop any segment that doesn't apply — order never changes.

| Segment | What it is | Required? | Rules |
|---|---|---|---|
| **Set Anchor** | Painting title (artist cards) · Subject (everything else) | always | This is what the design's set is named after. Painting titles should identify the subject when freshly named ("Kobe Shirt Pull", "MJ in Flight"); established art titles that don't ("Court Dreams") are fine — the folder and tracker carry the subject. |
| **Parallel** | Treatment line from the vocabulary (Legendary, …) | when the design has one | Must match the `PARALLELS` list in the tracker, spelled identically. A one-off design with no parallel may use a plain descriptor here ("Gum Card", "Lego Figure"). |
| **Variant** | Sub-treatment within the parallel (Gold, Angel Rare Air, …) | only with a parallel | One flat string — no sub-variants. Must be in that parallel's variant list. Omit for the parallel's base design. |
| **Tier** | Run size | limited runs only | `1of1` for one-of-ones, `of2` `of3` `of10` for runs. Omit when unlimited/undecided. |
| **Product** | Derivative type | derivatives only | `Plate` (graded plate), `Box` (custom box). Omit for the card itself. |

**Files inside the design folder:**

```
<full design name>.ai            ← exactly one, neutral name (never "Front.ai")
<full design name> - Front.pdf
<full design name> - Back.pdf
```

**Folder name** = the full design name (no Front/Back).
**App design name** = the identical string, character for character.

---

## Does the name include the subject?

**No separate subject segment.** The set anchor carries it:

- Non-artist cards: the anchor **is** the subject ("Kerry Wood - Gum Card - of3").
- Artist cards: the painting title *should contain* the subject's recognizable name when you're naming a previously unnamed painting ("Kobe Shirt Pull", not "Shirt Pull"). A real title like *Court Dreams* stays as-is — don't rename art to fit the file system.

Adding "Michael Jordan - " in front of "MJ in Flight" would say everything twice and make every filename longer; the Dropbox subject folder and the tracker already answer "who is this?" for the rare title that doesn't.

---

## Examples (current designs, renamed)

| Today | Under the key |
|---|---|
| Kobe Legendary - Gold (file: "Kobe Legendary Gold") | `Kobe Shirt Pull - Legendary - Gold - of2` |
| LeBron James - Legendary | `LeBron City Scape - Legendary` |
| Kobe Legendary (base) | `Kobe Shirt Pull - Legendary - of10` *(if the base runs /10)* |
| MJ in Flight - Leather GOAT 1/1 | `MJ in Flight - Leather - 1of1` |
| MJ in Flight - Angel Rare Air | `MJ in Flight - Angel - Rare Air - of10` |
| MJ in Flight - "Rare Air" - Halo 1/1 | `MJ in Flight - Angel - Halo - 1of1` |
| Black Mamba - Chrome Holographic | `Black Mamba Portrait - Holographic - Chrome - of2` |
| Black Mamba on Snake Skin (custom box) | `Black Mamba Portrait - Snake Skin - 1of1 - Box` |
| Court Dreams - Purple 1/1 (graded plate) | `Court Dreams - Purple - 1of1 - Plate` |
| Soccer – William Legendary | `William - Legendary` *(or painting-style anchor if it gets one)* |
| Kerry Wood - Bubble Gum Art | `Kerry Wood - Gum Card - of3` |

---

## Don'ts

- **No ` - ` inside a segment value** — it's the separator. ("Angel Rare Air" ✓, "Angel - Rare Air" ✗)
- **No slashes in filenames** (`1/1` is illegal on Windows — use `1of1`). Use plain hyphens, not en-dashes (–).
- **No sub-variants.** "Angel Rare Air" is one variant, not Angel → Rare Air.
- **Don't put the year, "final", "v2", or "new"** in design names — version inside the .ai, archive old exports.
- **Don't invent parallel/variant spellings** — if it's not in the tracker vocabulary, add it there first, then name the file.

---

## How the sync will use this (planned)

Split the name on ` - `, then validate left to right: anchor must match a known painting or subject → parallel must be in `PARALLELS` → variant must be in that parallel's list → tier must match `1of1|ofN` → product in `{Plate, Box}`. A name that parses fills `parallel`/`variant` automatically; a name that doesn't gets a naming alert in the tracker instead of silent guessing.

**Status (2026-06-16):** the parallel vocabulary is now settled — Black Mamba Portrait (Holographic: Chrome/Satin/Snake · Snake Skin) and MJ in Flight (Angel: base/Clear Air/Rare Air/Halo · Clear: Glass · Stained Glass · Space · Leather). Every design passes the key with **zero naming alerts**. Dropbox/app renames can proceed; the sync parser can then be built against this vocabulary.
