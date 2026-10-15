# F09 — Enquiry + Visit

**Feature root:** `src/features/f09_enquiry_visit/`

F09 provides property, project and general enquiry forms; visit-request preferences; status/history presentations; and reschedule, cancellation and follow-up draft interfaces.

## Entry points

- General enquiry: `/enquiry`
- Property enquiry: `/enquiry?kind=property&id=<known-property-id>&mode=enquiry`
- Property visit draft: `/enquiry?kind=property&id=<known-property-id>&mode=visit`
- Project enquiry: `/enquiry?kind=project&id=<known-project-id>&mode=enquiry`
- Project visit draft: `/enquiry?kind=project&id=<known-project-id>&mode=visit`

The route resolves IDs through the existing property/project preview catalog. Display names and locations come from those local records, not user-controlled query strings. Missing or unknown property/project IDs return not-found instead of silently falling back to a general enquiry.

## Scope

### Enquiry
- Property, project and general enquiry forms.
- Contact-channel preference and contact-detail validation.
- Qualification and purchase-timeframe preferences.
- Confirmation and status presentations.
- Service-backed enquiry-history interface.

### Visit
- In-person and video-walkthrough request preferences.
- Preferred date, time window and IANA time zone.
- Attendee count, access requirements and additional notes.
- Visit status and confirmation presentation.
- Rescheduling and cancellation draft interfaces.
- Post-visit feedback draft and visit-history interface.

## Current integration boundary

The authorized enquiry and scheduling services are not connected in this preview. The service flags in `enquiry.constants.ts` must remain `false` until the corresponding server-side integrations exist and have been verified.

A draft callback hands data to its caller in memory. It does not send an enquiry, notify a broker, reserve a visit or change an existing appointment.

Do not generate fake reference numbers or represent locally prepared drafts as server-confirmed records.

## Data and privacy

- Do not write contact details or enquiry drafts to browser storage, URLs, logs or analytics.
- Do not introduce client-side calls to internal ACRL or `AUTONOMY_ENGINE` runtime modules.
- Do not read Control Center state as live frontend data.
- Enquiry and visit history views accept records returned by an authorized service; local drafts are not history records.
- Collect contact and accessibility details only for the purpose explained by the relevant form and applicable privacy notice.

## Module responsibilities

| Module | Responsibility |
|---|---|
| `enquiry.types.ts` | Enquiry targets, drafts, statuses and validation types |
| `visit.types.ts` | Visit drafts, statuses, history and action types |
| `enquiry.constants.ts` | Options, service flags and shared validators |
| `EnquiryWorkspace.module.css` | Feature-scoped responsive styling |
| `EnquiryContactDetails.tsx` | Shared contact-detail fields |
| `EnquiryContactPreference.tsx` | Contact-channel selection |
| `EnquiryQualification.tsx` | Qualification and timeframe |
| `PropertyEnquiryForm.tsx` | Property enquiry draft form |
| `ProjectEnquiryForm.tsx` | Project enquiry draft form |
| `GeneralEnquiryForm.tsx` | General enquiry draft form |
| `EnquiryConfirmation.tsx` | Enquiry confirmation/status presentation |
| `EnquiryStatus.tsx` | Enquiry status presentation |
| `EnquiryHistory.tsx` | Authorized enquiry history |
| `VisitDateTimeSelector.tsx` | Visit format, date, time and time zone |
| `VisitRequestForm.tsx` | Visit-request draft form |
| `VisitConfirmation.tsx` | Visit confirmation/status presentation |
| `VisitStatus.tsx` | Visit status presentation |
| `VisitReschedule.tsx` | Rescheduling-request draft |
| `VisitCancel.tsx` | Cancellation-request draft |
| `VisitFollowUp.tsx` | Post-visit feedback draft |
| `VisitHistory.tsx` | Authorized visit history |

## Verification

From `REOS_CONTROL_CENTER/Frontend`, run:

```bash
npm run verify:f09
npm run typecheck
npm run lint
npm run build
