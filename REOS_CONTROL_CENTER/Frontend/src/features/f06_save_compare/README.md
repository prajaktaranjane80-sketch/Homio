# F06 — Save, Compare & Return

Canonical location:

`REOS_CONTROL_CENTER/Frontend/src/features/f06_save_compare/`

## Experience components

F06 uses the existing components and shared design system:

- `SavedShell.tsx`
- `SavedProperties.tsx`
- `SavedProjects.tsx`
- `SavedLocalities.tsx`
- `SavedSearches.tsx`
- `RecentViews.tsx`
- `CompareShell.tsx`
- `CompareProperties.tsx`
- `CompareProjects.tsx`
- `CompareLocalities.tsx`
- `CompareTable.tsx`
- `CompareCriteria.tsx`
- `CompareSummary.tsx`
- `CompareActions.tsx`
- `ShareComparison.tsx`
- `SavedEmptyState.tsx`
- `CompareEmptyState.tsx`
- `saved.types.ts`
- `compare.types.ts`
- `SavedCompareExperience.module.css`

The `/saved` and `/compare` routes compose these existing
components. Route-specific duplicate stylesheets must not be
introduced.

## Data and identity

`saveCompareAdapters.ts` maps Search, Property and Project
records into F06 presentation records.

Saved and compared item identity is the combination of
entity kind and ID. A property and project with the same
ID must remain separate items.

The comparison store allows at most four items and removal
must respect entity kind.

## Persistence

Current implementation uses in-memory browser-session state.

- A full page reload clears the store.
- Account persistence is not connected.
- Cross-device synchronization is not connected.
- A copied URL does not restore records in a separate browser.
- Do not claim that saved items are permanently stored.

## Data truth

Missing facts must display as missing. Do not invent pricing,
availability, verification or inventory.

Do not invent successful enquiry, appointment or transaction
outcomes.

## Architecture boundaries

F06 must not import ACRL or AUTONOMY_ENGINE runtime modules.
It must not read `REOS_CONTROL_CENTER/data/state.json` at runtime.

## Verification

`npm run verify:f06` runs the F06 static contract gate.
The repository verification script includes the F06 gate
before TypeScript, lint and production build checks.

A static contract gate does not replace a successful TypeScript
check, lint run or production build.
