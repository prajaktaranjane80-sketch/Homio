# F02 — Home Discovery

F02 owns the HOMIO homepage discovery experience, including LP03–LP30, its page composition, homepage React components, and their CSS modules.

## Ownership

- `src/app/page.tsx`: homepage route composition only.
- `HomeDiscoveryPage.tsx`: F02 homepage composition.
- Other TSX and CSS modules in this directory: homepage-specific implementation.
- `src/components/shell`, `src/components/navigation`, and `src/components/ui`: shared application shell and UI primitives.
- F04 and F05: property and project detail experiences.

## Architecture boundaries

- Do not create frontend-owned business truth.
- Do not import ACRL or AUTONOMY_ENGINE into frontend runtime.
- Do not read Control Center state as live frontend data.
- Do not claim unverified inventory, prices, availability, ownership, or backend capabilities.
- Do not link to fictional app routes.
- Keep component-to-component imports relative within F02.