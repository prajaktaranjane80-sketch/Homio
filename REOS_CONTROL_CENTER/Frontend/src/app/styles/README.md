# HOMIO F01 — Design System

The shared design system is the foundation for HOMIO / REOS frontend
features. Preserve existing components, exports, routes and integrations
when making visual changes.

## Canonical visual direction

- Charcoal: #111111
- Ivory: #F8F7F4
- Champagne gold: #C59B63
- White: #FFFFFF

Gold is a restrained accent. Preserve meaningful success, warning, error
and information colours. Keep keyboard focus visible and respect reduced
motion preferences.

## Canonical styles

- `tokens.css` — shared design tokens
- `base.css` — reset, typography defaults, focus states and base primitives
- `foundation.css` — shared shell, navigation, forms, cards and UI states
- `motion.css` — lightweight motion utilities and reduced-motion behaviour
- `../globals.css` — global stylesheet entry point

Use existing tokens and components before introducing new variables,
duplicate controls or separate theme systems. Do not add network-dependent
font loading or animation dependencies without a demonstrated need.

## Verification

Run the following commands from `REOS_CONTROL_CENTER/Frontend`:

1. `npm run verify:lockfile`
2. `npm run verify:design-system`
3. `npm run verify:foundation`
4. `npm run typecheck`
5. `npm run lint`
6. `npm run build`

Run `npm run verify` for the complete existing frontend regression suite.

A Part 1 PASS requires actual successful command output and a desktop/mobile
browser review. Do not mark the part PASS based only on file presence or
static source inspection.
