# Our Dinner Table — Feature Roadmap

Prioritized from the landscape research and gap analysis. Ordered by a mix of user value, effort, and what builds on existing infrastructure.

---

## Phase 1: Quick Wins (low effort, immediate value)

These are small additions that punch above their weight — a few hours each, no architectural changes.

### 1. Ingredient Substitution Suggestions
**Effort:** Very low (AI prompt, one new button)
**Why now:** The recipe detail sheet already has an AI remix section. Adding a "What can I swap?" button is the same `sample.json()` call with a different prompt. Daily value while cooking — "I don't have heavy cream" is a real moment that happens mid-recipe.

### 2. Recipe Export as JSON
**Effort:** Very low (serialize `S.recipes`, trigger download)
**Why now:** Data portability is table stakes, and right now there's no backup path. If the artifact DB has a bad day, the recipe box is gone. One button on the Recipes tab, reusing the existing `downloads` capability.

### 3. Nutrition-Aware Plan Generation
**Effort:** Very low (prompt change only)
**Why now:** The AI already estimates nutrition per recipe. Adding an optional calorie/macro target to the planning prompt ("aim for roughly 600 cal per serving") costs nothing but a settings field and a few lines in the prompt string. Not transformative, but free.

### 4. Customizable Aisle Order
**Effort:** Low (UI for reordering a 12-item list, persist to settings)
**Why now:** The aisle list is hardcoded as `AISLES` constant. Letting users drag or reorder it to match their Hy-Vee's actual layout makes the shopping list immediately more useful in-store. Small change, real friction reduction.

---

## Phase 2: Core Improvements (medium effort, high value)

These take a bit more work but address the biggest pain points users report across the category.

### 5. Offline Shopping List
**Effort:** Medium (service worker, IndexedDB cache)
**Why:** The #1 complaint across every meal planning app is the shopping list dying on bad signal in the store. The current app is fully online — no connectivity, no list. A service worker that caches the page + a snapshot of the current week's shopping data in IndexedDB would make the list available offline. The check-off state syncs back when connectivity returns.
**Depends on:** Nothing. Can be done independently.

### 6. Batch Cooking / Cook-Once-Eat-Many Workflow
**Effort:** Medium (data model change + UI + AI prompt updates)
**Why:** The Sunday prep rollup already exists. The missing piece is a "batch" flag on a planned meal that says "cook 2x on Sunday, assign leftovers to Tuesday and Wednesday." This reduces the week from 7 cooking nights to 4–5 — exactly what the target family needs. Needs: a way to mark a meal as batch, a way to assign leftover servings to other nights (without double-counting on the shopping list), and AI awareness of batch opportunities when planning.
**Depends on:** Nothing, but natural to pair with Phase 1 nutrition work.

### 7. Recipe Import from Photos / Screenshots
**Effort:** Medium (reuse fridge-scan pipeline, new UI flow)
**Why:** The photo→AI→structured-data pipeline already works for fridge inventory. The same approach handles recipe cards, cookbook pages, and screenshots of recipe websites. Users have recipes in places URL import can't reach — handwritten cards, Instagram screenshots, cookbook photos. New "Import from photo" button in the Recipes tab, same `sample.json()` with images, different prompt targeting recipe structure instead of ingredient inventory.
**Depends on:** Image support in `sample()` (same constraint as fridge scanning).

---

## Phase 3: Polish & Differentiation (medium-high effort, nice-to-have)

These round out the experience but aren't blocking daily use.

### 8. Drag-and-Drop Week Rearrangement
**Effort:** Medium (touch event handling, swap logic)
**Why:** Currently you tap a day → pick sheet → choose recipe. Swapping two days or moving a dinner from Wednesday to Thursday means clearing one and re-picking. Drag-and-drop on the week view would make rearranging faster. Not critical — the tap flow works — but it's the interaction model users expect from a calendar.

### 9. Family Meal Voting
**Effort:** Medium (new UI flow, data model for vote collection)
**Why:** When the AI suggests a week, household members could vote on the options before the plan is finalized. Interesting for families where "what's for dinner" is a negotiation. Lower priority because the current app already has post-hoc voting (loved it / not a hit) that feeds back into future AI plans — voting before the plan is a workflow change, not a gap.

### 10. Calendar Export (.ics)
**Effort:** Low
**Why:** Export the week's dinners to Google Calendar or Outlook. Nice for families that live in their calendar, but low priority since the app itself is the canonical view. Could be a simple "Add to calendar" button on the week view.

---

## Parked (not worth pursuing now)

| Feature | Why parked |
|---------|-----------|
| **Grocery delivery integration** | Requires API partnerships with Instacart/AmazonFresh. High effort, uncertain availability, and the copy-to-clipboard flow covers the 80% case |
| **Expense tracking** | Interesting for shared households, but this is a family app — not the core problem being solved |
| **Multiple meal types** | Breakfast/lunch/snack would triple the scope. "Dinner only" is a deliberate focus, not a missing feature |
| **Plain-text recipe format** | Cool for developers (Cooklang), but adds complexity with no user-facing benefit for this family |
| **Self-hosting / auth system** | Currently on Artifact runtime. If it migrates to a standalone app, auth becomes necessary — but that's a platform decision, not a feature |

---

## Suggested Sequence

```
Now          Phase 1: Substitutions → Export → Nutrition target → Aisle order
Next         Phase 2: Offline list → Batch cooking → Photo recipe import
Later        Phase 3: Drag-and-drop → Voting → Calendar export
```

Phase 1 items can ship independently in any order. Phase 2 items are also independent but each takes a focused session. Phase 3 is gravy.
