
# F12 — Globalization & Market Activation

F12 provides HOMIO's global market-selection and activation-policy
presentation layer.

## Activation policy

- Pune, India is the designated active market.
- Other configured markets are built for future activation but are
  not operationally active.
- Market activation status is not proof that a business service is live.
- Inventory, enquiries, visits, brokerage, deal flow and other operations
  require their own verified REOS service integration and authorization.
- Do not display fabricated live inventory, confirmed appointments,
  transaction states, availability or operational metrics.

## Initial modules

- `market-activation.types.ts` — typed market and capability contracts.
- `market-activation.constants.ts` — market registry and selector options.
- `market-activation.utils.ts` — market lookup and display-policy helpers.
- `MarketSelector.tsx` — accessible market selection experience.
- `MarketSelector.module.css` — responsive premium F12 visual system.
- `MarketActivationBadge.tsx` — reusable activation status.
- `MarketStatus.tsx` — activation and service-readiness disclosure.

## Architecture boundaries

- REOS remains the canonical business authority.
- Client-side status utilities are presentation helpers, not access control.
- Never treat a selected market, email verification or UI status as
  authorization for restricted business data.
- Do not import ACRL, AUTONOMY_ENGINE or Control Center state into
  frontend runtime modules.
- Reuse existing HOMIO UI foundations where they already meet the
  component contract; do not create duplicate global UI primitives.

## Design direction

- Premium international SaaS presentation.
- Responsive layouts for mobile, tablet and desktop.
- Keyboard-accessible controls and visible focus states.
- Explicit active, built, unavailable and verification-required states.
- Reduced-motion support.
