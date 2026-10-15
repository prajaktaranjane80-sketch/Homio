# F10 — Transaction Workspace

HOMIO's transaction experience for consumers and authorized professionals.

## Responsibilities

- Present the current transaction state returned by an authorized service.
- Summarize the property, parties, offer, negotiation, documents, milestones,
  financial status, commission status and completion requirements.
- Show the next action only when it is included in the supplied transaction data.
- Keep the overview, documents and timeline understandable across screen sizes.
- Provide a typed boundary for future REOS transaction-service integration.

## Files

- `TransactionShell.tsx` — Main responsive workspace and section navigation.
- `DealOverview.tsx` — Deal summary and the supplied next action.
- `DealParties.tsx` — Participants and their supplied roles.
- `DealProperty.tsx` — Property context.
- `OfferSummary.tsx` — Offer terms provided by the service.
- `OfferStatus.tsx` — Consistent offer-state presentation.
- `NegotiationPanel.tsx` — Service-provided negotiation entries.
- `DocumentChecklist.tsx` — Supplied document requirements and states.
- `TransactionMilestones.tsx` — Supplied milestone timeline.
- `TransactionFinancialStatus.tsx` — Supplied transaction financial summary.
- `TransactionStatus.tsx` — Consistent transaction-state presentation.
- `CommissionStatus.tsx` — Supplied commission information.
- `DealCompletion.tsx` — Supplied completion state and checklist.
- `TransactionAccessNotice.tsx` — Explains the server-authorized data boundary.
- `TransactionEmptyState.tsx` — Safe state when no transaction data is supplied.
- `transaction.types.ts` — Read-only view models and action request types.
- `transaction.constants.ts` — Labels, status tones and formatting helpers.
- `TransactionWorkspace.module.css` — Feature-scoped responsive styling.

## Integration and security boundary

This feature is a presentation layer. It does not become the canonical source
of transaction, identity, authorization, payment, commission, document or
completion truth.

- A server-side integration must authenticate the viewer and authorize access
  to the requested transaction.
- The service must return only the fields that this viewer is permitted to see.
- Every action must be re-authorized by the server when executed.
- UI button state is not an authorization control.
- No status is changed locally to simulate a successful transaction action.
- Do not place transaction or personal data in browser storage, query strings,
  analytics or console logs.
- Do not import ACRL/AUTONOMY_ENGINE runtime modules or read Control Center
  state as application data.
- Do not add mock records that could be mistaken for real transactions.
- Until a verified service is connected, the workspace must show its
  no-data state rather than fabricated deal details.

## Styling

All styles belong in `TransactionWorkspace.module.css`. Avoid global CSS
selectors and inline styling for layout. Components should use semantic
headings, visible focus states and responsive layouts.

## Completion criteria

- All transaction information comes from typed input data.
- Unknown or missing data is presented honestly.
- Server-supplied actions are dispatched without locally changing business
  state.
- Mobile, tablet and desktop layouts remain usable.
- Type checks, lint, production build and focused F10 verification pass.
