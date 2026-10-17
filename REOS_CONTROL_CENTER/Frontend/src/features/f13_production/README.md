# F13 — Production Quality Support

F13 provides reusable frontend quality guardrails for HOMIO. Runtime integration is deliberately diagnostic-first: quality warnings do not mutate listing, enquiry, visit, account or transaction state.

## Integrated responsibilities

- Responsive viewport and horizontal-overflow diagnostics
- Accessibility checks for accessible names, form labels, image alt text and a main landmark
- SEO metadata helper used by the home and search routes
- Allowlisted image wrapper connected to the existing featured-project cards
- Image loading, fetch-priority and quality policy
- React error boundary applied at the root layout
- F13 loading boundary used by the route loading UI
- Shared compare-empty-state copy policy
- Production auth/app URL/analytics-sink configuration checks through Next instrumentation
- Privacy-safe analytics and conversion event contracts
- Browser runtime diagnostics

## Governance and data boundaries

- F12 owns market activation. A route existing does not mean its market inventory or operations are active.
- Property and project preview records must not be described as verified inventory.
- F13 does not own inventory, authentication, enquiries, visits or deal state.
- Do not import ACRL or AUTONOMY_ENGINE into frontend runtime.
- Do not read Control Center files as live frontend data.
- Analytics event properties are default-deny and only explicitly approved dimensions pass.
- No third-party analytics provider is configured by this layer. When analytics is enabled without a sink, production instrumentation logs a warning instead of pretending events are delivered.
- Production guard findings log codes and safe messages only; secret values are never logged.
- Home and search metadata remain `noIndex` while they expose experience-preview inventory. Change this only when source-backed inventory and market activation policy explicitly authorize indexing.

## Verification

Run from `REOS_CONTROL_CENTER/Frontend`:

- `npm run verify:f13`
- `npm run typecheck`
- `npm run lint`
- `npm run build`

The F13 verifier checks file presence and the key app integrations. CI must pass after these replacements are saved to the canonical branch.
