import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, "..");

const requiredFiles = [
  "src/app/search/page.tsx",
  "src/features/f03_search/SearchShell.tsx",
  "src/features/f03_search/SearchShell.module.css",
  "src/features/f03_search/SearchResults.tsx",
  "src/features/f03_search/SearchResultCard.tsx",
  "src/features/f03_search/SearchFilterDrawer.tsx",
  "src/features/f03_search/SearchAdvancedFilters.tsx",
  "src/features/f03_search/SearchBudgetFilter.tsx",
  "src/features/f03_search/SearchPagination.tsx",
  "src/features/f03_search/SearchIntentTabs.tsx",
  "src/features/f03_search/SearchLocationField.tsx",
  "src/features/f03_search/SearchSortBar.tsx",
  "src/features/f03_search/SearchViewToggle.tsx",
  "src/features/f03_search/SearchResultCount.tsx",
  "src/features/f03_search/SearchSummary.tsx",
  "src/features/f03_search/SearchActions.tsx",
  "src/features/f03_search/SearchMapView.tsx",
  "src/features/f03_search/search.types.ts",
  "src/features/f03_search/search.constants.ts",
  "src/features/f03_search/search.utils.ts",
  "src/features/f03_search/search-preview-catalog.ts",
  "src/features/f04_property/property-preview-catalog.ts",
  "src/features/f05_project/project-preview-catalog.ts",
];

const forbiddenRuntimeReferences = [
  "data/state.json",
  "HOMIO_REOS_MASTER_ARCHITECTURE.json",
  "ACRL",
  "AUTONOMY_ENGINE",
];

function absolute(relativePath) {
  return path.join(frontendRoot, relativePath);
}

function read(relativePath) {
  return fs.readFileSync(absolute(relativePath), "utf8");
}

function normalizeWhitespace(value) {
  return value.replace(/\s+/g, " ").trim();
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

for (const relativePath of requiredFiles) {
  assert(
    fs.existsSync(absolute(relativePath)),
    `Missing required F03 file: ${relativePath}`,
  );
}

assert(
  !fs.existsSync(absolute("src/app/search/page.module.css")),
  "Search route must not own feature styling.",
);

const route = read("src/app/search/page.tsx");
const searchShell = read("src/features/f03_search/SearchShell.tsx");
const results = read("src/features/f03_search/SearchResults.tsx");
const resultCard = read("src/features/f03_search/SearchResultCard.tsx");
const drawer = read("src/features/f03_search/SearchFilterDrawer.tsx");
const actions = read("src/features/f03_search/SearchActions.tsx");
const mapView = read("src/features/f03_search/SearchMapView.tsx");

const searchCatalog = read(
  "src/features/f03_search/search-preview-catalog.ts",
);

const searchUtils = read(
  "src/features/f03_search/search.utils.ts",
);

/*
 * Normalize whitespace so a phrase split across JSX lines cannot
 * create a false verification failure.
 */
const normalizedMapView = normalizeWhitespace(mapView);

assert(
  route.includes('from "@/features/f03_search/SearchShell"') &&
    route.includes("<SearchShell />"),
  "Search route must compose the F03 SearchShell.",
);

assert(
  !route.includes("useState") &&
    !route.includes("SearchResults"),
  "Search route must not own feature orchestration or result state.",
);

assert(
  !searchShell.includes("SAMPLE_RESULTS") &&
    searchShell.includes("SEARCH_PREVIEW_CATALOG") &&
    searchShell.includes("filterSearchCatalog"),
  "SearchShell must use the shared Search preview catalog.",
);

assert(
  searchCatalog.includes("getAllPropertyPreviews") &&
    searchCatalog.includes("getAllProjectPreviews"),
  "Search catalogue must reuse the F04 property and F05 project adapters.",
);

assert(
  searchCatalog.includes("filters.budgetCurrency") &&
    searchCatalog.includes("filters.budgetMin") &&
    searchCatalog.includes("filters.budgetMax") &&
    searchCatalog.includes("filters.areaMin") &&
    searchCatalog.includes("filters.areaMax") &&
    searchCatalog.includes("filters.furnishing") &&
    searchCatalog.includes("filters.amenities") &&
    searchCatalog.includes("filters.builder") &&
    searchCatalog.includes("filters.possession") &&
    searchCatalog.includes("filters.verifiedOnly"),
  "Search catalogue does not apply every declared advanced filter.",
);

assert(
  searchShell.includes("SearchIntentTabs") &&
    searchShell.includes("SearchLocationField") &&
    searchShell.includes("SearchPagination"),
  "Search intent, location and pagination controls must be wired.",
);

assert(
  searchShell.includes("searchStateFromParams") &&
    searchShell.includes("searchStateToParams") &&
    searchShell.includes("popstate"),
  "Search URL state must restore from parameters and browser history.",
);

assert(
  results.includes("SearchListView") &&
    results.includes("SearchMapView"),
  "SearchResults must expose both list and location-preview modes.",
);

assert(
  drawer.includes("SearchAdvancedFilters") &&
    drawer.includes("onApply") &&
    drawer.includes("onClose"),
  "Filter drawer must support draft edits, apply and cancel/close.",
);

assert(
  searchUtils.includes("filterProject") &&
    searchUtils.includes("budgetCurrency") &&
    searchUtils.includes("resetSearchState"),
  "Search utility contract is missing separate project filter, currency or reset semantics.",
);

assert(
  actions.includes("searchStateToParams") &&
    actions.includes("disabled") &&
    actions.includes("Saved-search persistence"),
  "Share must serialize current state and unsupported saved-search writes must be disabled.",
);

/*
 * The preview must never manufacture geographic marker coordinates.
 * The disclosure phrase is checked after whitespace normalization.
 */
assert(
  !mapView.includes("left: `${15 +") &&
    !mapView.includes("top: `${18 +") &&
    normalizedMapView.includes("authoritative coordinates"),
  "Location preview must not invent marker coordinates.",
);

assert(
  resultCard.includes("Illustrative image") &&
    resultCard.includes("Media not connected") &&
    resultCard.includes("entityType"),
  "Search cards must distinguish illustrative assets and project/property entities.",
);

for (const forbidden of forbiddenRuntimeReferences) {
  for (const [name, content] of [
    ["search route", route],
    ["SearchShell.tsx", searchShell],
    ["SearchResults.tsx", results],
    ["search-preview-catalog.ts", searchCatalog],
    ["SearchFilterDrawer.tsx", drawer],
  ]) {
    assert(
      !content.includes(forbidden),
      `Forbidden runtime reference in ${name}: ${forbidden}`,
    );
  }
}

console.log("F03 SEARCH CONTRACT GATE = PASS");
console.log(`FILES VERIFIED = ${requiredFiles.length}`);
console.log("SHARED PROPERTY + PROJECT CATALOGUES = PASS");
console.log("FILTER CONTRACT COVERAGE = PASS");
console.log("URL RESTORE + SHARE CONTRACT = PASS");
console.log("DRAFT/APPLY/CANCEL FILTER FLOW = PASS");
console.log("PAGINATION + INTENT CONTROLS = PASS");
console.log("NO SYNTHETIC MAP COORDINATES = PASS");
console.log("NO STATE.JSON RUNTIME = PASS");
console.log("NO ACRL RUNTIME = PASS");
