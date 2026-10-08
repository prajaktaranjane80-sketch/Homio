# F05 — Project & Collection Experience

F05 is the HOMIO project and collection discovery experience.

## Purpose

Help a consumer understand the larger opportunity surrounding one property,
project or project collection.

## Experience

Project entry
→ Project overview
→ Visual overview
→ Location
→ Project facts
→ Inventory summary
→ Available opportunities
→ Amenities
→ Trust
→ Related projects
→ Individual property
→ Continue discovery

## Frontend responsibility

F05 owns:

- project presentation
- collection presentation
- visual overview presentation
- location presentation
- project facts presentation
- inventory presentation
- project opportunity navigation
- save/compare/share interaction presentation
- responsive project experience
- loading state
- unavailable state
- error recovery

F05 does not own:

- canonical inventory
- property ownership
- project ownership
- builder authority
- lead ownership
- enquiry processing
- visit orchestration
- transaction state
- commission state
- trust/fraud authority

## REOS binding boundary

Production project and inventory data must come from approved
REOS capabilities.

F05 must not invent a project API, inventory engine or business contract.

## Preview data

`project.data.ts` currently provides a controlled experience-preview object
only so the production UX can be developed and visually verified.

Preview values are not canonical inventory or business truth.

## ACRL boundary

ACRL is not part of F05 runtime.

F05 must continue to build and render when ACRL is unavailable.

## Connected journey

Property
→ Project
→ Available opportunity
→ Property

The project route therefore acts as a contextual layer between individual
property discovery and broader project discovery.

## Definition of done

- Project route exists.
- Project metadata exists.
- Project visual overview exists.
- Project facts exist.
- Project location exists.
- Inventory summary exists.
- Opportunity inventory exists.
- Property navigation exists.
- Amenities exist.
- Trust treatment exists.
- Related projects exist.
- Save/compare/share presentation exists.
- Loading state exists.
- Not-found/unavailable state exists.
- Error recovery exists.
- Responsive layout exists.
- No ACRL runtime dependency exists.
- No state.json runtime dependency exists.
- No Master Architecture runtime dependency exists.
- No frontend inventory authority exists.
