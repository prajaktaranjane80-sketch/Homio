# F04 — Property Experience

F04 is the HOMIO consumer property-detail experience.

## Purpose

Help a consumer understand one property well enough to decide whether it
deserves further attention.

## Experience

Property entry
→ Media
→ Summary
→ Facts
→ Details
→ Project context
→ Amenities
→ Location
→ Trust
→ Disclosure
→ HOMIO AI
→ Similar discovery
→ Enquiry / Visit
→ Continue discovery

## Frontend responsibility

F04 owns:

- property presentation
- media presentation
- temporary UI state
- save/compare interaction presentation
- AI entry presentation
- enquiry/visit entry presentation
- loading state
- unavailable state
- responsive property experience

F04 does not own:

- canonical inventory
- property ownership
- verification authority
- lead ownership
- enquiry business processing
- visit orchestration
- transaction state
- commission state
- fraud/trust authority

## REOS binding boundary

The production property data source must come from an approved REOS
capability.

F04 must not invent a property API, inventory engine or business contract.

## ACRL boundary

ACRL is not part of F04 runtime.

F04 must continue to build and render without ACRL being available.

## Preview data

`property.data.ts` currently provides a controlled experience-preview object
only so the production UX can be developed and visually verified.

It is not canonical inventory and must not be treated as production business
truth.

## Definition of done

- Property route exists.
- Gallery exists.
- Core property summary exists.
- Property facts exist.
- Detailed information exists.
- Project context exists.
- Amenities exist.
- Location context exists.
- Trust and disclosure treatment exists.
- HOMIO AI entry exists.
- Similar discovery exists.
- Enquiry/visit entry exists.
- Loading state exists.
- Not-found/unavailable state exists.
- Responsive layout exists.
- No ACRL runtime dependency exists.
- No state.json runtime dependency exists.
- No master-architecture runtime dependency exists.
- No frontend inventory authority exists.
