# HOMIO F01 Experience Foundation — Change Set

Repository: `prajaktaranjane80-sketch/Homio`
Branch audited: `reos-development`

## Why this change is needed

The canonical branch contains the F01 React components, but the global styles only covered a small set of base primitives. The shell/header/navigation, global search, overlay dialogs, form controls, status components and responsive shared layout did not have a dedicated loaded foundation stylesheet. This change set adds that stylesheet and makes the existing global-search component perform a real navigation using the F03-supported `q` query parameter. It also removes a global shortcut that pointed every user to a sample project record.

## Apply in this order

The prefixes `ADD/` and `REPLACE/` are package labels and are not part of repository paths. Preserve the remainder of each path exactly.

1. **ADD** `REOS_CONTROL_CENTER/Frontend/src/app/styles/foundation.css` from `ADD/REOS_CONTROL_CENTER/Frontend/src/app/styles/foundation.css`.
2. **REPLACE** `REOS_CONTROL_CENTER/Frontend/src/app/globals.css`.
3. **REPLACE** `REOS_CONTROL_CENTER/Frontend/src/components/navigation/GlobalSearch.tsx`.
4. **REPLACE** `REOS_CONTROL_CENTER/Frontend/src/components/shell/ResponsiveNavigation.tsx`.
5. **REPLACE** `REOS_CONTROL_CENTER/Frontend/src/components/shell/Header.tsx`.
6. **REPLACE** `REOS_CONTROL_CENTER/Frontend/src/components/shell/GlobalActionLayer.tsx`.
7. **REPLACE** `REOS_CONTROL_CENTER/Frontend/scripts/verify-foundation.mjs` last, so the new style-contract gate is enabled only after its stylesheet is present.

Each replacement file in this package contains the complete file, not a partial patch. Do not delete any existing files.

## Targeted verification after all files are saved

Run from `REOS_CONTROL_CENTER/Frontend`:

`npm run verify:foundation`

The full `npm run verify` also runs F02–F05, TypeScript, lint and production build; keep the planned combined regression run for after all five layer parts are implemented. GitHub CI may run according to the repository's existing workflow triggers.

## Write-permission limitation

The connected GitHub integration allowed reading the canonical branch but returned HTTP 403 for GitHub file writes and branch creation. Therefore this package has not been committed to GitHub. The canonical branch remains unchanged by this assistant's attempted write operations.
