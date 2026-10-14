# F06 — Save, Compare & Return

**Canonical source location:** `REOS_CONTROL_CENTER/Frontend/src/features/f06_save_compare/`

F06 helps people collect promising options, compare meaningful differences, and return to the exact property/project/locality/search context without turning frontend code into a second source of business truth.

## Experience principles

- **Premium and futuristic, not an admin console:** luminous accent details, calm contrast, glass-like surfaces, fast scanning, large whitespace, and responsive comparison.
- **Decision-first comparison:** show only supplied attributes that help a user decide; missing facts are shown as “Not supplied”. Never infer price, availability, verification or property facts.
- **Progressive disclosure:** start with the essentials; let users enable/disable comparison groups.
- **Responsive:** rich desktop comparison table, horizontally scrollable labelled comparison on tablet, and stacked decision cards on mobile.
- **Return continuity:** preserve each supplied record's original `href`; do not invent route destinations.
- **Truthful persistence status:** components accept source-provided records as props. Empty arrays mean empty states. They do not fabricate sample inventory or claim account persistence.

## Files

- `SavedShell.tsx` — shared Saved workspace and categories/search.
- `SavedProperties.tsx`, `SavedProjects.tsx`, `SavedLocalities.tsx` — typed saved record views.
- `SavedSearches.tsx` — saved search contexts when supplied by an approved adapter.
- `RecentViews.tsx` — recent navigation records supplied by a history adapter.
- `CompareShell.tsx` — comparison workspace, category selector, and criteria state.
- `CompareProperties.tsx`, `CompareProjects.tsx`, `CompareLocalities.tsx` — category-specific comparison composition.
- `CompareTable.tsx` — attribute matrix; missing values are never guessed.
- `CompareCriteria.tsx` — progressive disclosure of decision-relevant groups.
- `CompareSummary.tsx`, `CompareActions.tsx`, `ShareComparison.tsx` — count/context, explicit actions, share URL.
- `SavedEmptyState.tsx`, `CompareEmptyState.tsx` — clear, helpful empty states.
- `saved.types.ts`, `compare.types.ts` — F06 presentation contracts.
- `SavedCompareExperience.module.css` — shared responsive premium visual system.

## Boundaries before production wiring

1. Feed the components from verified property/project/locality/search adapters; do not put a mock catalogue in this feature.
2. Saved records and comparison state must be supplied by an approved service/session adapter. This package does **not** claim that user-account persistence is connected.
3. Do not import ACRL/AUTONOMY_ENGINE modules or read `REOS_CONTROL_CENTER/data/state.json` at runtime.
4. The `href` on each record must come from the canonical route/data adapter. Do not invent a route when one is absent.
5. Wire `SavedShell` and `CompareShell` into approved route composition only after `/saved` and `/compare` are accepted in the frontend route contract. This bundle intentionally does not add route files or claim CI verification.
6. Use the project's existing `Image`/link, auth, API and verification conventions when wiring adapters. No credentials or sensitive session data belong in browser storage.

## Inputs

Every data component receives explicit typed props. Without data, it renders a genuine empty state rather than fake listings. The `persistenceStatus` notice in `SavedShell` must be set by the parent from actual integration status.
