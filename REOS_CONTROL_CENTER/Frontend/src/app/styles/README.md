# HOMIO F01 — Design System

The shared design system is the foundation for HOMIO / REOS frontend
features. Preserve existing components, exports, routes and integrations
when making visual changes.

## Canonical visual direction — Rosewood & Almond

HOMIO uses one four-colour brand palette across the shared shell and
feature interfaces:

- Rosewood: #6F334B — primary brand colour for branding, primary actions,
  active navigation and key emphasis.
- Ballet Blush: #F3DDE4 — soft feminine surfaces, selected states and subtle
  highlights.
- Almond Cream: #F8F1E7 — primary page and surface background.
- Espresso Cocoa: #352A2D — use sparingly for fine lines, dots and restrained
  decorative details, not as the dominant text or surface colour.

White may be used as a neutral content surface for readable cards and forms;
it is not a fifth brand accent.

Use Rosewood for readable headings and interface text. Keep contrast clear
on Blush and Almond backgrounds. Avoid spreading pink across every surface
or using Cocoa as a large-area fill. Semantic success, warning, error and
information colours remain separate from the four-colour brand palette.

## Canonical styles

- `tokens.css` — single source of truth for palette, typography, spacing,
  focus, elevation and motion tokens.
- `base.css` — reset, typography defaults, focus states and base primitives.
- `foundation.css` — shared shell, navigation, forms, cards and UI states.
- `motion.css` — lightweight motion utilities and reduced-motion behaviour.
- `../globals.css` — global stylesheet entry point.

Use existing tokens and components before introducing new variables,
duplicate controls or separate theme systems. Use a consistent Rosewood
focus treatment across shared controls. Keep Cocoa details subtle. Do not
add network-dependent font loading or animation dependencies without a
demonstrated need.

Motion should be restrained and consistent: 140 ms micro-interactions,
220 ms standard transitions, 420 ms reveals, one shared easing system and a
single 1400 ms skeleton shimmer token. Respect `prefers-reduced-motion` and
do not animate property imagery with scale or zoom effects.

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
