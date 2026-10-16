# F13 — Production Quality Support

F13 provides production guardrails for the HOMIO frontend.

## Responsibilities
- Responsive layout checks
- Accessibility audit helpers
- SEO metadata defaults
- Image and performance policies
- Error and loading boundaries
- Consistent empty-state messages
- Privacy-safe analytics event contracts
- Conversion event contracts
- Production configuration checks
- Browser runtime diagnostics

## Architecture boundaries
- F12 owns market activation.
- A route existing does not mean that market inventory or operations are active.
- F13 does not own inventory, authentication, enquiries, or deal state.
- Do not import ACRL or AUTONOMY_ENGINE into frontend runtime.
- Do not read Control Center files as live frontend data.
- Analytics must never receive passwords, tokens, contact details,
  owner documents, or enquiry message content.

## Verification
Run:
- npm run verify:f13
- npm run typecheck
- npm run lint
- npm run build
