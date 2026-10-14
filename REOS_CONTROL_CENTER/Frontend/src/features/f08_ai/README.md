# F08 — HOMIO AI

## Purpose

F08 is HOMIO's real-estate decision-support experience. It helps a visitor express a property brief, prepare search criteria, review comparison factors and continue into existing HOMIO discovery and account experiences.

## Canonical location

`REOS_CONTROL_CENTER/Frontend/src/features/f08_ai/`

## Included experience

- Natural-language brief capture and local conversation preview.
- Search launch using the existing F03 route and query conventions.
- Budget guidance using the currencies currently supported by F03.
- Property and project comparison by reusing the F06 session store.
- Locality comparison checklist with links into Search.
- Rental, investment-readiness and market-review checklists.
- Property notes, validation errors, empty states and service status.
- Responsive layout using HOMIO's black, ivory and champagne design tokens.

## Service boundary

`AI_LIVE_SERVICE_CONNECTED` is intentionally false.

This implementation does not connect to a live AI model, market-data feed, affordability engine or brokerage-handoff service. The conversation preview is static disclosure text, property notes remain local component state, and comparison data comes from the existing F06 browser-session store.

Do not label the preview output as AI-generated, verified or submitted.

## Architecture rules

- Reuse F03 search routes and search parameters.
- Reuse F06 comparison state; do not introduce a second compare store.
- Do not import ACRL or AUTONOMY_ENGINE in frontend runtime code.
- Do not read Control Center state files from the browser.
- Do not invent listings, locality scores, current prices, rental yields, appreciation or legal conclusions.
- Keep the experience responsive and respect reduced-motion preferences.
- Never add provider keys or service secrets to client components.

## Route and verification

- Route: `/ai`
- Focused gate: `npm run verify:f08`
- Full gate: `npm run verify`
