# F07 — My HOMIO

My HOMIO is the signed-in user's private real-estate decision workspace.

Canonical root:

`REOS_CONTROL_CENTER/Frontend/src/features/f07_my_homio/`

## Product architecture

F07 combines four experiences:

- Personal account and identity-provider profile claims.
- Search activity, saved requirements, recent views, and shortlist return paths.
- Existing F06 Save and Compare workspace.
- Enquiry, conversation, visit, recommendation, journey, document,
  notification, and preference service entry points.

The information architecture takes inspiration from activity-led
real-estate portals while preserving HOMIO's own global product identity.

## Source-of-truth rules

- Authenticated identity comes from the existing server-validated
  HOMIO session.
- Saved properties and comparison selections reuse F06's existing store.
- Recent searches and recently viewed properties/projects are captured
  from genuine frontend interactions and held in browser-tab session storage.
- A saved search is a local session requirement, not a delivered property alert.
- No sample property, enquiry, message, visit, transaction or document is
  represented as a real user record.

## Service integration boundaries

The authenticated account currently does not provide authoritative feeds
for enquiries, conversations, visits, brokerage milestones, recommendations,
documents or notifications. Those sections are service-ready workspace
surfaces; they must not imply that a backend operation has happened.

Connecting any of those capabilities requires an approved service adapter,
typed response contract, authorization check, loading/error states and tests.

## Component ownership

- `MyHomioShell.tsx`: responsive personal workspace and navigation.
- `MyHomioDashboard.tsx`: actual activity summary and return actions.
- `MyHomioProfile.tsx`: read-only profile claims from the authenticated session.
- `MyHomioSaved.tsx`, `MyHomioCompare.tsx`: reuse F06's shared store.
- `MyHomioRecentSearches.tsx`: actual recent and saved search requirements.
- `MyHomioRecentViews.tsx`: actual property/project views.
- Remaining page components: purpose-specific account service workspaces.
- `myHomioActivityStore.ts`: validated session-only activity store.
- `MyHomio.module.css`: F07 responsive visual system.

## UX and accessibility

- Uses HOMIO's shared black, ivory and champagne design tokens.
- Supports narrow mobile screens, keyboard focus and visible selected states.
- Uses semantic navigation and section headings.
- Counts and activity summaries must derive from real session data.
- Missing backend records are not replaced with illustrative sample records.

## Architecture boundaries

F07 must not import ACRL or AUTONOMY_ENGINE runtime modules.
It must not read `REOS_CONTROL_CENTER/data/state.json` at runtime.
It must preserve the protected `/my` route and existing sign-out endpoint.

## Verification

`npm run verify:f07` checks the F07 contract.
The full verification command must also run TypeScript, ESLint,
and the Next.js production build.
