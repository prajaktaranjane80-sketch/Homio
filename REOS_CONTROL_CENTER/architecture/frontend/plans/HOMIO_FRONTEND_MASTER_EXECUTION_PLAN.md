# HOMIO / REOS — Master Frontend Engineering & Execution Blueprint

**Document status:** Proposed consolidated master specification  
**Project:** HOMIO / REOS — Pune-first real-estate platform  
**Primary purpose:** Govern frontend audit, architecture, design, implementation, testing, release and cross-chat continuity through one authoritative document.  
**Canonical destination:** `REOS_CONTROL_CENTER/architecture/frontend/plans/HOMIO_FRONTEND_MASTER_EXECUTION_PLAN.md`

---

## 1. Mission and engineering standard

Build a premium, production-grade real-estate platform with the quality, reliability and usability expected from a leading SaaS product.

The frontend must be:
- Visually cohesive, premium, responsive and user-friendly.
- Pune-first, with architecture that supports future Indian and international expansion.
- Modular, maintainable, testable and secure.
- Designed for buyers, tenants, owners, brokers, builders, administrators and authorized enterprise users.
- Fast, accessible, commercially viable and measurable.
- Easy for a new development chat to understand and continue without losing context.

**Non-negotiable:** Do not confuse a polished plan with completed implementation. Every completion claim must be supported by actual repository evidence and relevant test results.

## 2. The 360° audit verdict

The previous separate frontend execution-plan and coding-structure documents should be consolidated because they overlap and can create ambiguity about which document governs implementation.

The earlier documents are planning inputs, not proof that the existing frontend has been fully audited or meets production standards.

The consolidated master must resolve these 12 audit domains:

1. Existing project structure, source files and dependencies.
2. Canonical plans, task state and conflicting instructions.
3. File ownership, module boundaries and dependency direction.
4. Design tokens, typography, color, spacing and component consistency.
5. Navigation, responsive UX, accessibility and user journeys.
6. Real-estate domain models, listings, search and enquiry workflows.
7. Authentication, authorization, tenant isolation and SaaS roles.
8. API boundaries, input validation, privacy and security.
9. Automated tests, regression coverage and failure handling.
10. Performance, loading states, media optimization and Core Web Vitals.
11. Production configuration, observability, release safety and rollback.
12. Documentation, evidence, duplication control and cross-chat handoff.

For each domain, record the actual finding, affected files, risk, required action, verification method and evidence. Do not mark a domain PASS merely because a plan describes the intended solution.

## 3. Authority and source-of-truth rules

Before implementation, inspect the live repository and establish the current branch, HEAD commit, relevant files and current task state.

Respect the existing project authority hierarchy:
- `REOS_CONTROL_CENTER/data/state.json` governs machine-readable execution state and gates.
- `reos-development` is the canonical code and history reference.
- The existing frontend execution plan and blueprint remain audit inputs until their unique requirements and references are reconciled.
- CI results and evidence must identify the exact code revision they validate.

Do not silently alter task state, invent acceptance results, or claim that a file has been saved, a test has passed or a release is complete without verification.

If authority sources conflict, stop the affected implementation, document the conflict and resolve it through the project's established governance process.

## 4. Baseline audit before coding

Inspect the current repository before creating or replacing files.

Required baseline:
- Confirm current branch and commit SHA.
- Read the existing frontend structure, execution plan and implementation blueprint.
- Inspect actual application entry points, routes, components, styles, assets, API clients, package scripts and test configuration.
- Inspect the existing design-system verifier at `REOS_CONTROL_CENTER/Frontend/scripts/verify-design-system.mjs`.
- Identify existing reusable components and working user journeys.
- Check imports, dependency direction, duplicated implementations and dead-code candidates.
- Identify incomplete features, broken routes, placeholder content, inconsistent styling and unhandled errors.
- Check available CI workflows and the latest run tied to the relevant commit.

Produce a file inventory and findings register before proposing large structural changes.

Every finding must be labelled one of:
- **PASS:** Verified against a defined criterion.
- **FAIL:** A reproducible issue exists.
- **BLOCKED:** Verification requires missing access, dependency or evidence.
- **NOT RUN:** Verification has not occurred.
- **NOT APPLICABLE:** A documented reason makes the check irrelevant.

Do not report a clean audit when significant files or evidence remain unexamined.

## 5. Architecture and file ownership

Use the repository's actual working architecture as the starting point. The following is a target model, not permission to create every directory immediately.

```text
src/
  app/
    routing/
    providers/
    layouts/
  components/
    ui/
    navigation/
    feedback/
  features/
    f01-foundation/
    f02-auth/
    f03-discovery/
    f04-search/
    f05-property-details/
    f06-enquiries/
    f07-user-dashboard/
    f08-owner-broker-tools/
    f09-builder-tools/
    f10-saas-administration/
    f11-payments-and-monetization/
    f12-notifications/
    f13-platform-integrations/
  lib/
    api/
    validation/
    permissions/
    analytics/
    utilities/
  styles/
    tokens/
    globals/
```

First reconcile these conceptual boundaries with the actual F01–F13 feature definitions, existing source files and approved project plans. Preserve established naming where changing it would cause needless churn.

### File-level ownership register

For every existing or proposed file, record:
- Exact repository path.
- Current status: existing, proposed, modified, consolidated or retirement candidate.
- Purpose and accountable module.
- Public exports and consumers.
- Dependencies and permitted dependency direction.
- Related feature and acceptance criteria.
- Tests and verification evidence.
- Migration or deletion risks.

A file must have one clear responsibility. Do not introduce a new file when an existing file already provides the correct responsibility and can be safely improved.

Do not create placeholder modules, duplicate utilities, parallel design systems or multiple competing route definitions.

## 6. Design system and visual consistency

The entire site must use one coherent design system. Page-specific variation is allowed only when it serves a real usability or brand purpose.

### Core palette

- Rosewood: `#6F334B`
- Ballet Blush: `#F3DDE4`
- Almond Cream: `#F8F1E7`
- Espresso Cocoa: `#352A2D`
- White: `#FFFFFF`

Audit the existing use of Champagne Gold `#C59B63` and other legacy colors. Retain, map or remove them only after checking their purpose and visual impact.

Define semantic tokens for:
- Primary, secondary and accent colors.
- Text, muted text, surfaces and page backgrounds.
- Borders, focus rings, errors, warnings and success states.
- Typography scale, font weights, line heights and readable line lengths.
- Spacing, page gutters, content widths and responsive breakpoints.
- Border radii, shadows, overlays and layering.
- Motion durations, easing and reduced-motion behavior.

Use centralized tokens rather than scattered color values or one-off styling.

### Typography and layout

Use a consistent typography hierarchy and a restrained, readable type scale. Verify font licensing, loading behavior, fallback fonts and performance.

Every page must follow a coherent grid, spacing rhythm and responsive behavior. Avoid cramped cards, excessive decoration, inconsistent heading sizes and unnecessary full-screen sections.

### Motion and interaction

Animations should improve orientation, feedback or perceived responsiveness—not delay important actions.

Respect reduced-motion preferences. Avoid distracting motion, layout shifts, slow entrance sequences and animation that interferes with keyboard or touch interaction.

### Design acceptance

- All primary pages use the shared tokens and components.
- Interactive states are defined for hover, focus, active, disabled, loading, success and error where relevant.
- Contrast and focus visibility are verified.
- Mobile, tablet and desktop layouts are checked.
- Existing design-system verification passes or documented gaps are tracked.

## 7. UX and navigation requirements

The experience must be clean, premium and easy to understand—not crowded or dependent on endless scrolling.

Requirements:
- Clear navigation and predictable page hierarchy.
- Dedicated pages for substantial workflows instead of forcing everything into one long page.
- Search and filters that preserve useful context.
- Consistent breadcrumbs or back-navigation where appropriate.
- Helpful empty, loading, error and retry states.
- Clear form labels, validation and confirmation feedback.
- Responsive menus and usable touch targets.
- No broken links, dead buttons or misleading calls to action.
- No fake listing information, fabricated reviews or unsupported trust claims.

Do not open a new page for every tiny interaction. Use a modal, drawer or inline state when it is genuinely simpler. Choose dedicated routes for complex tasks that deserve their own workspace.

### Pune-first product direction

Prioritize useful Pune property discovery and locally relevant workflows. Design the architecture so future cities, regions and international markets can be added without hardcoding Pune-specific assumptions throughout the application.

Location, currency, measurement units, languages and region-specific rules should be handled through appropriate data and configuration boundaries.

## 8. Real-estate domain and workflow integrity

Audit the actual backend and API contracts before implementing frontend data structures.

Define and validate contracts for:
- Property listings and property types.
- Sale, rent and other supported transaction types.
- Location, price, area, amenities and listing status.
- Media, ownership and verification metadata.
- Search, sorting, filtering and pagination.
- Saved properties and comparison, where supported.
- Enquiries, lead attribution, consent and follow-up status.
- Builder, broker and owner workflows.
- Administrative moderation and audit trails.

Use typed, validated API boundaries where supported by the project's technology stack.

Represent loading, empty, partial, stale and failed data explicitly. Never present mock data as live production data.

Do not invent backend capabilities. If a required API or domain rule does not exist, record the dependency and implement only the frontend behavior that is valid under the agreed contract.

## 9. Authentication, SaaS tenancy and security

Verify the actual authentication system, permission model and backend enforcement before designing role-specific interfaces.

Potential user categories include:
- Public visitor, buyer or tenant.
- Property owner.
- Broker or brokerage team member.
- Builder or developer.
- Enterprise or white-label tenant.
- Platform administrator.

These are conceptual categories; actual roles must match the project's approved authorization model.

Security requirements:
- Enforce authorization on the server, not just by hiding frontend controls.
- Do not expose secrets, private credentials or privileged configuration in client bundles.
- Validate untrusted input at the appropriate boundaries.
- Prevent unauthorized cross-tenant access.
- Avoid logging sensitive personal information.
- Apply safe handling to uploads, URLs and user-generated content.
- Use clear consent and privacy behavior for enquiries and analytics.
- Provide appropriate handling for expired sessions and denied access.
- Avoid leaking sensitive information in error messages.
- Verify dependencies and security-relevant configuration.

Do not claim that the frontend alone guarantees application security.

## 10. API, state and component engineering

Use a clear boundary between:
- Presentation components.
- Feature-level workflows and state.
- Shared domain utilities.
- API clients and data transformations.
- Authentication and permission helpers.

Avoid circular dependencies, duplicated API calls, unnecessary global state and direct coupling between unrelated features.

Use existing project conventions unless the audit proves a change is needed.

Components should have clear props, predictable behavior, accessible markup and testable responsibilities. Shared components must solve a genuine repeated need; do not create abstractions solely to increase the file count.

Handle network failures, timeouts, stale responses, repeated submissions and invalid responses appropriately for each workflow.

## 11. Accessibility, performance and responsiveness

Target WCAG 2.2 AA where applicable and verify against real pages and interactions.

Check:
- Keyboard navigation and visible focus.
- Semantic headings and landmarks.
- Form labels and actionable error messages.
- Accessible names for controls.
- Dialog focus handling.
- Color contrast and non-color status cues.
- Screen-reader feedback for asynchronous changes.
- Reduced-motion preferences.

Measure performance before declaring budgets. Establish explicit thresholds based on the real application, hosting and user journeys.

Review:
- Core Web Vitals.
- JavaScript bundle size and unnecessary dependencies.
- Image formats, sizing, lazy loading and layout stability.
- Font loading and render-blocking resources.
- Route-level code splitting where appropriate.
- Caching and network request duplication.
- Slow rendering and expensive component updates.

Test at representative mobile, tablet and desktop sizes. Do not claim performance improvements without comparable measurements.

## 12. Content and conversion quality

Use specific, truthful content that helps users make decisions.

Audit headings, property-card information, search guidance, calls to action, trust statements, form copy, empty states and error messages.

Prioritize:
- Clear property discovery.
- Useful location and price information.
- Transparent enquiry expectations.
- Credible and verifiable trust signals.
- Clear next steps.
- Accessible and concise wording.

Do not use generic filler, fabricated statistics, false scarcity or unverified claims about verification, security or market leadership.

Where research is required, record the source, date and relevant finding. Separate observed facts from assumptions and proposed product decisions.

## 13. Testing and verification

Use the existing test framework and CI structure wherever practical. Audit the current test suite before introducing another test system.

Required verification categories:
- Static analysis, linting and type checks where supported.
- Unit tests for utilities and business rules.
- Component tests for important interaction states.
- Integration tests for API and feature workflows.
- Route and navigation checks.
- Accessibility checks.
- Responsive and browser-level smoke tests.
- Regression tests for fixed defects.
- Security checks relevant to frontend dependencies and configuration.
- Production build and deployment validation.

Test critical user journeys end to end, including successful, empty, invalid, denied and failed states.

A passing test suite does not automatically prove that every acceptance criterion is satisfied. Record untested areas and known limitations.

## 14. Implementation order and change control

The canonical task state and approved dependency order determine what work may start. This document does not override project gates.

Recommended sequence, subject to the current task state:

1. Baseline repository and authority audit.
2. Reconcile existing plans, feature definitions and acceptance criteria.
3. Resolve the shared design system and application shell.
4. Establish or verify routing and navigation.
5. Implement approved feature workflows in dependency order.
6. Connect validated API contracts and permissions.
7. Complete accessibility, responsive and performance work.
8. Run regression and production verification.
9. Record evidence and update the authorized task state.
10. Prepare the next task and handoff.

Do not start downstream work when a required dependency is unresolved.

### Safe file changes

Before adding, modifying, consolidating or retiring files:
- Search for existing equivalents.
- Inspect imports, routes, tests, workflows and documentation references.
- Determine whether the change alters public interfaces.
- Preserve necessary compatibility or document the migration.
- Update consumers and tests together.
- Verify that no required functionality or unique requirement is lost.

Do not delete files solely because they appear old, duplicated or unused from a partial search. Confirm their references and purpose first.

## 15. Consolidation of the two previous planning documents

This master document is intended to become the single authoritative frontend engineering and execution specification.

The previous documents are:
- `REOS_CONTROL_CENTER/architecture/frontend/plans/HOMIO — Complete Frontend Website Master File & Module Structure`
- `REOS_CONTROL_CENTER/architecture/frontend/plans/HOMIO_FRONTEND_IMPLEMENTATION_BLUEPRINT.json`
- `REOS_CONTROL_CENTER/architecture/frontend/plans/HOMIO_FRONTEND_EXECUTION_PLAN.json`
- `REOS_CONTROL_CENTER/architecture/frontend/plans/HOMIO_FRONTEND_ULTRA_PRO_CODING_STRUCTURE.md`

Audit each existing path and its references before changing its status.

Migration procedure:
1. Identify unique requirements, task mappings, feature definitions and acceptance criteria in each source.
2. Map every required item to this master or to its proper machine-readable authority.
3. Resolve conflicts against canonical project state and established governance.
4. Verify that active workflows, scripts and documentation no longer depend on an obsolete planning path.
5. Retire redundant documents only when safe and authorized.
6. Preserve required historical evidence and machine-readable task state.
7. Record the migration and verify the resulting repository state.

Do not delete or replace the JSON execution plan merely because this Markdown document exists. Machine-readable task state and executable automation may still depend on it.

## 16. Definition of done

A frontend task is complete only when all applicable conditions are met:

- The task was authorized by the current project state.
- The exact target files and responsibilities were identified.
- The implementation follows the approved architecture and design system.
- Relevant user flows work with valid data and appropriate failure states.
- Security and authorization boundaries are respected.
- Relevant tests and static checks have run.
- The production build and applicable CI checks pass.
- Acceptance criteria are individually verified.
- Regressions and known limitations are recorded.
- Evidence identifies the exact commit and test or workflow run.
- Required documentation and task-state updates are made through the authorized process.

If any required condition remains unverified, report the task as pending, blocked or partially complete—not complete.

## 17. Evidence register

Maintain a traceable record for every implementation task.

| Field | Required information |
|---|---|
| Task ID | Canonical project task identifier |
| Requirement | Acceptance criterion or approved change |
| Files | Exact affected repository paths |
| Implementation | Concise description of the actual change |
| Tests | Commands or CI checks that were run |
| Result | PASS, FAIL, BLOCKED or NOT RUN |
| Revision | Exact commit SHA tested |
| Evidence | Relevant workflow run, test output or review reference |
| Remaining gaps | Known failures, limitations and follow-up work |

Never reuse evidence from an unrelated or outdated commit as proof for current code.

## 18. Cross-chat continuity and handoff

Every handoff must state:
- Canonical repository and branch.
- Current verified HEAD SHA.
- Current authorized task and its state.
- Exact files inspected or changed.
- Requirements completed and evidence supporting them.
- Failed, blocked and untested items.
- Decisions made and unresolved conflicts.
- The next authorized action and its dependencies.

A new chat must re-read current repository state before assuming that previous findings are still current. Do not rely on conversation history as a substitute for live verification.

## 19. Final engineering principle

Build the right solution, not the largest number of files.

Prioritize verified behavior, consistent design, clear architecture, secure workflows, measurable quality and maintainable code. Audit first, reuse intelligently, implement in authorized dependency order, test the actual result and preserve evidence.

**This document defines the intended standard. Its requirements become verified only when the repository implementation and supporting evidence demonstrate that they are satisfied.**
