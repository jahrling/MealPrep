# Our Dinner Table — Handoff Notes

Family dinner planner built as a single self-contained HTML page, published as a Claude Artifact and backed by its runtime `db`, `sample`, `downloads` and `user` capabilities. No build step, no external backend — everything lives in `dinner-table.html`.

**Live artifact:** https://claude.ai/artifact/Q9CPQKMd8mmVVyNhf11imq
**Source file:** `dinner-table.html` (downloaded alongside this note)

## Stack / runtime model

- Plain HTML/CSS/JS, one file, no framework, no build.
- State lives in the artifact's shared document store via `window.claude.use('db')` — see the collections below. Local `S` object in JS is a live mirror kept in sync with `onSnapshot` listeners.
- AI features go through `window.claude.use('sample')` (Claude, on the viewer's own account/usage, called from inside the page — no server, no API key).
- File download of the shopping list goes through `window.claude.use('downloads')`.
- `window.claude.use('user')` is used only to detect read-only viewers (`can('data.write')`).
- Capabilities are declared on publish: `{db:{}, sample:{}, user:{}, downloads:true}`.

If you continue this in Claude Code / as a normal web app instead of an Artifact, the two things that need re-homing are:
1. **Storage** — currently the artifact `db` (JSON documents, realtime, shared across viewers). Would become a real backend (e.g. Firestore, Supabase, or your own API) if this leaves the Artifacts runtime.
2. **AI calls** — currently `sample()`, which is Claude-in-the-page with no backend. Would become calls to the Anthropic API from your own server if rehosted.

Everything else (UI, rendering, business logic) is portable as-is; it's vanilla JS manipulating `innerHTML` from a single `S` state object with a `render()` function — no virtual DOM, no reactivity framework.

## Data model (`db` collections)

- `recipes/<id>` — one document per recipe. Shape (see `normRecipe()` in the JS for the authoritative version):
  ```
  {
    name, blurb, protein, veg: [string], newFlavor: bool,
    kidTip, prepAhead, servings,
    scratch: { time, ingredients: [{name, amt, unit, aisle}], steps: [string] },
    shortcut: { same shape as scratch },
    nutrition: {cal, protein, fiber} | null,
    rating: {up, down},
    source: 'starter' | 'ai' | 'web',
    sourceUrl: string,   // link back to the original site, when source === 'web'
    created
  }
  ```
- `plans/<YYYY-MM-DD>` — one document per week (keyed by that week's Sunday). `{ days: {0..6: {recipeId, mode, servings, ai?}} , notes }`. `ai: true` marks a night the AI picked, so "Redo AI picks" can target only those.
- `shop/<YYYY-MM-DD>` — per-week shopping-list state: `{ have: {itemKey: bool}, got: {itemKey: bool}, extras: [{id, name, qty, aisle}] }`. The list itself is *derived* at render time from that week's `plans` doc + `recipes`, not stored.
- `pantry/staples` — single doc, `{ items: [{name, aisle}] }`. Long-lived staples (salt, oil, etc.) that default to "already have" on every week's list.
- `inventory/current` — single doc, `{ items: [{name, qty, aisle}], updated }`. The "On hand" list from fridge/cabinet photo scans (see below). Also defaults to "already have" on the shopping list.
- `settings/family` — `{ servings }`.

## Key features implemented

- **Week tab** — 7-day dinner calendar, servings stepper, Sunday-prep rollup (pulled from each recipe's `prepAhead`), notes field, "Fill open nights with AI," "Redo AI picks" (re-plans only nights the AI chose, leaving manually-picked nights alone), per-night "Suggest something else" (single-night AI swap that avoids repeating recipes already declined).
- **Recipes tab** — search/filter (favorites, quick, new-flavor, AI-made), every recipe has a from-scratch *and* a shortcut version (toggle), votes (loved it / not a hit) feed back into AI planning, AI "remix" (faster / more veggies / more kid-friendly / new flavor), **manual/AI recipe import from a web link** (paste ingredients + directions, optionally have Claude structure it and add a shortcut version; keeps a "From the web" chip linking back to the source).
- **Shop tab** — three views: shopping list (aisle-grouped, derived from the week's planned recipes, scaled by servings), On hand (photo-scanned or hand-entered current inventory), Pantry (long-term staples). Shopping list supports check-off, "have it" toggle, free-text extras, copy-to-clipboard, and **file download** (`downloads` capability) as a `.txt`.
- **Ideas tab** — "Plan my week" (fills open nights, can invent 1-2 new recipes), "Cook from what you have" (freeform fridge contents *or* one-tap fill from the On-hand list), "Create a recipe" (freeform request → full recipe with both versions).
- **Fridge/cabinet inventory** — in-app photo capture calls `sample.json()` with the photos attached to identify food items (aisle-categorized), reviewed/checked before merging into `inventory/current`. *Caveat:* image sending via `sample()` was not available for this artifact in testing (both the Claude app and web at time of writing) — the in-app UI degrades gracefully with a message pointing back to this chat, where Claude reads photos directly and writes to `inventory/current` via the `ArtifactData` tool. If/when image support lands for this surface, the in-app flow should work unmodified — nothing else needs to change.
- Read-only handling throughout (`user.can('data.write')`), debounced writes with per-path queues, optimistic local state with `onSnapshot` as source of truth.

## Known gaps / next steps

- No true camera capture (relies on the OS file picker, per Artifact runtime constraints) — fine for now, but a native app would let you shoot straight to the scan flow.
- No image-in-sample fallback UI beyond the message pointing at chat; worth revisiting once/if that capability opens up for artifacts.
- No auth/multi-household support — sharing is whatever the Artifact's own Share menu provides (owner + explicitly-invited editors).
- No print/export beyond the shopping-list `.txt` download.
- Ingredient parsing for manually-typed or "save as I typed it" web recipes doesn't split amount/unit from name (each line is stored as a single ingredient string) — only the AI-formatted path structures ingredients properly for scaling and shopping-list quantities.
