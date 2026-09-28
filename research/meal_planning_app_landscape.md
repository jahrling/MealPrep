# Meal Planning App Feature Landscape

Research survey of open-source and commercial meal planning apps, compiled 2026-09-27.

---

## Open-Source Projects Surveyed

| Project | Description | Stars (approx.) |
|---------|-------------|-----------------|
| [Mealie](https://github.com/mealie-recipes/mealie) | Self-hosted recipe manager + meal planner. Vue frontend, REST API backend. Strong URL import and household management. | ~7k |
| [Tandoor Recipes](https://github.com/TandoorRecipes/recipes) | Full-featured recipe manager with meal planning, shopping lists, nutrition calculation, and multi-user permissions. | ~6k |
| [Grocy](https://grocy.info/) | "ERP beyond your fridge" — inventory/stock tracking, meal planning, shopping lists, expiration tracking, chore management. | ~7k |
| [KitchenOwl](https://github.com/TomBursch/kitchenowl) | Flutter-based grocery list + recipe manager. Real-time shared lists, expense tracking for shared households. | ~2k |
| [Cooklang](https://cooklang.org/) | Plain-text recipe markup language + CLI tools. Not an app per se, but a recipe data format with an ecosystem of parsers, apps, and plugins. | ~1k |

Commercial/freemium apps also surveyed: Eat This Much, Plan to Eat, Paprika 3, Mealime, Prepear, FoodiePrep, MealThinker, MealSync, Cooklist, Samsung Food.

---

## Common Features (Table Stakes)

Present in most or all apps surveyed.

### Recipe Management

- Import recipes from URL (scrape structured data from recipe websites)
- Manual recipe entry with structured fields (ingredients, steps, times, servings)
- Recipe search, tagging, and categorization
- Serving size scaling
- Recipe collections / cookbooks

### Meal Planning

- Calendar/weekly view for assigning meals to days
- Meal type slots (breakfast, lunch, dinner, snack)
- Drag-and-drop rearrangement
- Random meal suggestion / "what should I eat?" button

### Shopping Lists

- Auto-generate shopping list from a meal plan or selected recipes
- Combine and deduplicate ingredients across multiple recipes
- Check-off items while shopping
- Categorize items by store aisle/section

### Nutrition

- Per-recipe calorie and macronutrient calculation (protein, carbs, fat)
- Daily/weekly nutrition summaries tied to the meal plan

### Multi-User / Sharing

- Share recipes via link
- Household/family accounts with shared meal plans and shopping lists
- Permission controls (viewer vs. editor)

### Data & Privacy

- Self-hosted option (all major open-source projects)
- Import/export recipes (JSON, various proprietary formats)

---

## Unique / Standout Features

These appear in only one or a few apps and represent genuine differentiation.

### Pantry / Inventory Awareness
**Found in:** Grocy, FoodiePrep, Cooklist

Track what you already have at home. Suggest recipes that use up existing stock. Grocy's "Due Score" ranks recipes that use ingredients about to expire — a real food-waste reducer.

### Automatic Plan Generation from Constraints
**Found in:** Eat This Much

Set calorie/macro targets, dietary restrictions, budget, and number of meals — the app generates a full plan. Swap or lock individual meals while it recalculates the rest. Most apps only let you manually assign recipes.

### Plain-Text Recipe Format
**Found in:** Cooklang

Recipes as version-controllable `.cook` files. Ingredients, cookware, and timers marked with `@`, `#`, `~` syntax. Portable, future-proof, no vendor lock-in. Has Obsidian and VS Code plugins.

### Family Voting on Meals
**Found in:** MealSync

Household members vote on meal options before the plan is finalized.

### Supermarket-Aware Sorting
**Found in:** Tandoor, KitchenOwl

Shopping lists sorted according to the layout of your specific supermarket, not just generic categories.

### Grocery Delivery Integration
**Found in:** Eat This Much, Samsung Food

Generate shopping lists that push directly to Instacart or AmazonFresh for delivery.

### Expense Splitting
**Found in:** KitchenOwl

Track and split grocery costs among roommates/housemates — unique to shared-living scenarios.

### LLM-Powered Planning
**Found in:** MealThinker

Chat-first interface that remembers pantry, preferences, and recent meals. Generate a week's plan from one conversational prompt.

### Calendar Export
**Found in:** Tandoor

Export meal plans as `.ics` to integrate with Google Calendar, Outlook, etc.

### Real-Time Synced Shopping
**Found in:** KitchenOwl, Tandoor

Multiple people can check off items on the same shopping list simultaneously with live sync.

### Mood / Time-Based Suggestions
**Found in:** MealTap

"I have 20 minutes and feel like something light" — instant filtered suggestions.

---

## Gaps — Commonly Requested, Rarely Done Well

Based on Reddit discussions, app store reviews, and forum threads.

### Offline Access
Most web-based apps fail when you're in a store with bad signal. Native apps with offline caching are rare in the open-source space.

### Flexible Recipe Import
Users have recipes scattered across screenshots, PDFs, handwritten notes, and random websites. Most importers only handle structured recipe schema from well-known sites. OCR/AI import from photos is almost nonexistent in open-source.

### Dietary Restriction Filtering That Actually Works
Users with multiple restrictions (e.g., gluten-free + low-FODMAP + vegetarian) find that most filter systems are shallow — they tag recipes but don't deeply understand ingredient substitutions.

### "What Can I Make With What I Have?"
Pantry-first planning exists in a few apps (Grocy, FoodiePrep) but is often bolted on rather than being the core flow. Users want this to be fast and friction-free.

### Batch Cooking / Meal Prep Support
Planning for cooking once and eating multiple times. Few apps handle portions-across-days, leftover tracking, or "cook Sunday, eat Monday–Wednesday" workflows natively.

### Quick Editing and Low Tap Count
Many apps are over-designed. Users abandon them when it takes too many taps to add Tuesday's dinner. The apps that survive daily use are the ones that feel like a notepad, not an ERP.

### Nutrition-Aware Plan Generation
Most apps show nutrition *after* you plan, but very few help you *plan toward* a nutrition target automatically. Eat This Much is the exception, but it's commercial.

### Ingredient Substitution Suggestions
"I don't have heavy cream — what can I use?" is a natural question while cooking. Almost no app handles this.

---

## Gap Analysis: "Our Dinner Table" vs. the Landscape

How the current app (mealprep_v02.html) stacks up against the features surveyed above.

### Table Stakes — Already Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Recipe URL import | **Done** | "Add from web" flow; AI can structure pasted ingredients/directions |
| Manual recipe entry | **Partial** | Via web-import sheet (name, ingredients, steps, time). No standalone "new recipe" form — recipes come in through AI or web import |
| Recipe search & filtering | **Done** | Search by name/protein/veg, filter by favorites/quick/new-flavor/AI-made |
| Serving size scaling | **Done** | Per-recipe stepper, ingredients scale proportionally |
| Weekly calendar view | **Done** | 7-day grid with day stamps, today highlight |
| Meal type slots | **Partial** | Dinner only (by design — "Our Dinner Table"). No breakfast/lunch/snack |
| Drag-and-drop rearrangement | **No** | Tap-to-pick flow instead; no drag-and-drop |
| Random / AI suggestion | **Done** | "Plan my week," per-night "Suggest something else," "Cook from what you have" |
| Auto-generate shopping list | **Done** | Derived from planned recipes, combined/deduped, scaled by servings |
| Check-off while shopping | **Done** | Per-item check-off with got/ungot toggle |
| Aisle categorization | **Done** | 12 aisles, regex-based auto-assignment, Hy-Vee-oriented |
| Nutrition per recipe | **Done** | Cal/protein/fiber estimated by AI, shown on recipe detail |
| Multi-user sharing | **Partial** | Artifact share model (owner + invited editors), read-only detection. No household accounts |
| Import/export | **Partial** | Shopping list copy/download as .txt. No recipe export (JSON, etc.) |

### Standout Features — Already Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Pantry / inventory awareness | **Done** | Three-tier: Pantry staples + On-hand inventory + per-week "have it" overrides. All feed into shopping list |
| Fridge photo scanning | **Done** | Photo → AI inventory extraction → reviewed checklist → merge to On-hand list |
| AI plan generation | **Done** | Fills open nights, respects family votes, balances proteins, uses on-hand food, shortcut mode on weeknights |
| LLM-powered recipe creation | **Done** | Freeform request → full recipe with scratch + shortcut versions |
| AI remix | **Done** | Rework a recipe for speed/veggies/kid-friendly/new-flavor |
| Real-time synced data | **Done** | Firestore-style onSnapshot listeners; shared across viewers |
| Dual recipe versions | **Done** | Every recipe has scratch + shortcut, toggled in-line. Unique differentiator |
| Sunday prep rollup | **Done** | Aggregates prepAhead notes from planned recipes into one list |
| Family rating system | **Done** | Thumbs up/down per recipe; AI planning uses votes to favor/avoid |

### Standout Features — Not Yet Implemented (Worth Considering)

| Feature | Effort | Value | Notes |
|---------|--------|-------|-------|
| **Supermarket-specific aisle sorting** | Low | Medium | Currently uses generic 12-aisle list. Could let users reorder aisles to match their store's layout |
| **Calendar export (.ics)** | Low | Low | Export the week's dinners to Google Calendar / Outlook |
| **Family voting on upcoming meals** | Medium | Medium | Let household members vote on AI suggestions before finalizing the plan |
| **Grocery delivery integration** | High | Medium | Push list to Instacart/AmazonFresh. API integration required |
| **Expense tracking** | Medium | Low | Track grocery spending per week. Not core to meal planning |

### Gaps — Worth Addressing

| Gap | Current State | Opportunity |
|-----|--------------|-------------|
| **Offline access** | No offline support; web-only, needs connectivity | Service worker + IndexedDB cache would let the shopping list work in-store with bad signal. High value |
| **Flexible recipe import (photos/screenshots)** | AI structures pasted text from web. No photo/OCR import of recipes | Already have photo→AI for fridge scanning; same pipeline could handle recipe card/screenshot→structured recipe. Medium effort, high value |
| **"What can I make with what I have?"** | **Done well** — freeform text input + one-tap fill from On-hand list. One of the app's strengths |
| **Batch cooking / meal prep support** | Sunday prep notes exist but are freeform text. No "cook once, eat 3 days" workflow | Could add a "batch" flag: cook on Sunday, auto-assign leftovers to Monday–Wednesday. Reduces the plan from 7 cooking nights to 4–5. High value for the target family |
| **Low tap count / friction** | Good — single-file app, quick pick flows, no login wall | Drag-and-drop on the week view would save taps. "Quick plan" (one-tap fill entire week) already exists |
| **Nutrition-aware plan generation** | AI shows nutrition after planning. No "plan toward 2000 cal/day" mode | Could add calorie/macro targets to the AI planning prompt. Low effort (prompt change), medium value |
| **Ingredient substitution** | Not implemented | Natural fit for the existing AI remix flow — "I don't have X, what can I use?" button on the recipe detail sheet. Low effort |
| **Recipe export** | Shopping list only (copy/download .txt) | Export recipe box as JSON for backup/migration. Low effort, important for data portability |
| **Drag-and-drop week planning** | Not implemented | Reorder/swap dinners by dragging on the calendar. Medium effort (touch handling), nice-to-have |
| **Multiple meal types** | Dinner only | Breakfast/lunch/snack would be a significant scope expansion. Current "dinner only" focus is a feature, not a bug, for this family |
