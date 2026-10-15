
# F11 — HOMIO Professional SaaS

Feature root: `src/features/f11_professional/`

## Purpose

A premium, responsive professional workspace for approved HOMIO operations.
It is a presentation layer over authorized REOS capabilities, not a separate
business engine.

## Authorized role categories

- HOMIO
- HOMIO authorized brokerage operators
- Builders
- Owners or authorized inventory partners
- Enterprise / white-label partners when permitted by architecture

A category in this list does not itself grant access. The server must verify
the current user's role, organization scope, requested record and permitted
operation before returning data or executing an action.

## Required modules

- `ProShell.tsx`
- `ProDashboard.tsx`
- `ProInventory.tsx`
- `ProInventoryDetail.tsx`
- `ProLeads.tsx`
- `ProEnquiries.tsx`
- `ProVisits.tsx`
- `ProFollowUps.tsx`
- `ProClients.tsx`
- `ProProjects.tsx`
- `ProDeals.tsx`
- `ProDocuments.tsx`
- `ProPerformance.tsx`
- `ProWorkspace.tsx`
- `pro.types.ts`

`ProWorkspace.module.css` and any focused support components are feature-scoped
presentation modules.

## Security boundary

- A valid login session is not proof of professional authorization.
- Do not fabricate lead, client, enquiry, visit, project, inventory or deal data.
- Do not generate synthetic performance metrics or success states.
- Do not infer role or organization membership from email, display name or URL.
- Every future record read and mutation must be authorized server-side.
- Do not store professional records or contact information in browser storage.
- Do not import ACRL / AUTONOMY_ENGINE runtime modules.
- Do not read Control Center `state.json` as frontend application data.

## Explicitly prohibited

- Broker Directory
- Broker Comparison
- Broker Bidding
- Lead Auction
- Competing Broker Marketplace

## Current preview behavior

The professional authorization and data capabilities remain disconnected until
their verified server-side REOS integrations are implemented. The workspace
must disclose this state instead of displaying demo records as real data.

## Completion criteria

- Exact feature root and required module ownership are preserved.
- Routes are not redirected to the public homepage.
- Login return paths allow only reviewed internal routes.
- The UI makes no unsupported role, inventory, deal or performance claims.
- Responsive styles, keyboard focus and reduced-motion behavior are covered.
- F11 verification, TypeScript, lint and production build pass.
