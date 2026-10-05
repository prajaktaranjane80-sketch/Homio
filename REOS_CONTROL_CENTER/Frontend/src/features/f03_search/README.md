# F03 — HOMIO Search Experience

## Purpose

F03 is the consumer search and discovery layer for HOMIO.

It sits after the homepage discovery experience and before property/project
result experiences.

Primary responsibilities:

- search intent
- location discovery
- property/project search criteria
- filter composition
- search state
- result presentation
- saved search handoff
- HOMIO AI handoff

## Supported Intents

- Buy
- Rent
- Commercial
- Projects
- Land

## Global Architecture Rule

HOMIO is globally designed from day one.

Market activation is separate from product structure.

Pune is the first operational market.

Other markets may have UI, routes and feature structure built in advance,
but they must not become operationally active until the corresponding market
is activated.

## Consumer Journey

Homepage
→ Search
→ Results
→ Property / Project
→ Save / Compare
→ Enquiry
→ Visit
→ HOMIO Brokerage

## Search Principles

1. Location is a first-class search object.
2. Intent is explicit.
3. Filters remain extensible.
4. Search state must be URL-safe and shareable.
5. Search UI must support desktop, tablet and mobile.
6. Search must not depend on ACRL.
7. Search must not read state.json.
8. Search must not import backend runtime modules.
9. Search must remain independent of broker marketplace concepts.
10. Search may hand off to HOMIO AI without becoming AI runtime itself.

## Planned F03 Structure

- SearchShell
- SearchHeader
- SearchIntentTabs
- SearchLocationField
- SearchSuggestionPanel
- SearchPropertyType
- SearchBudgetFilter
- SearchBedroomFilter
- SearchAreaFilter
- SearchPropertyStatus
- SearchFurnishingFilter
- SearchAmenityFilter
- SearchProjectFilter
- SearchBuilderFilter
- SearchPossessionFilter
- SearchVerificationFilter
- SearchAdvancedFilters
- SearchFilterDrawer
- SearchSortBar
- SearchViewToggle
- SearchResultCount
- SearchResults
- SearchResultCard
- SearchMapView
- SearchListView
- SearchEmptyState
- SearchErrorState
- SearchLoadingState
- RecentSearches
- SavedSearches
- PopularSearches
- SearchSummary
- SearchActions
- SearchPagination

## Non-Goals

F03 must not implement:

- broker marketplace
- broker bidding
- lead auction
- competing broker directory
- backend transaction logic
- ACRL runtime behaviour

## Future Integration Boundaries

F03 may later connect to:

- HOMIO Search APIs
- Property inventory
- Project inventory
- Locality data
- Market activation
- Saved searches
- HOMIO AI
- analytics / conversion events

Those integrations must be added without changing the consumer-facing
search contract.
