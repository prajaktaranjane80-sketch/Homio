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
  "src/features/f03_search/SearchFilterDrawer.tsx",
  "src/features/f03_search/SearchSortBar.tsx",
  "src/features/f03_search/SearchViewToggle.tsx",
  "src/features/f03_search/SearchResultCount.tsx",
  "src/features/f03_search/SearchSummary.tsx",
  "src/features/f03_search/SearchActions.tsx",
  "src/features/f03_search/search.types.ts",
  "src/features/f03_search/search.constants.ts",
  "src/features/f03_search/search.utils.ts",
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
const drawer = read("src/features/f03_search/SearchFilterDrawer.tsx");
const featureCss = read("src/features/f03_search/SearchShell.module.css");

assert(
  route.includes('from "@/features/f03_search/SearchShell"') &&
    route.includes("<SearchShell />"),
  "Search route must compose the F03 SearchShell.",
);

assert(
  !route.includes("SAMPLE_RESULTS") &&
    !route.includes("useState") &&
    !route.includes("SearchResults"),
  "Search route must not own search orchestration or result state.",
);

assert(
  searchShell.includes("SAMPLE_RESULTS") &&
    searchShell.includes("SearchResults") &&
    searchShell.includes("SearchFilterDrawer"),
  "F03 SearchShell must own search orchestration, results and filters.",
);

assert(
  results.includes("SearchListView") && results.includes("SearchMapView"),
  "SearchResults does not expose both list and map modes.",
);

assert(
  drawer.includes("SearchAdvancedFilters"),
  "SearchFilterDrawer is not wired to SearchAdvancedFilters.",
);

assert(
  !searchShell.includes("verified: true") &&
    searchShell.includes("verified: false"),
  "Preview search data must not manufacture verification.",
);

assert(
  featureCss.includes(".toolbar") && featureCss.includes(".pageNote"),
  "Feature stylesheet is missing search layout styles.",
);

for (const forbidden of forbiddenRuntimeReferences) {
  for (const [name, content] of [
    ["search route", route],
    ["SearchShell.tsx", searchShell],
    ["SearchResults.tsx", results],
    ["SearchFilterDrawer.tsx", drawer],
  ]) {
    assert(
      !content.includes(forbidden),
      `Forbidden runtime reference in ${name}: ${forbidden}`,
    );
  }
}

console.log("F03 SEARCH INTEGRATION = PASS");
console.log(`FILES VERIFIED = ${requiredFiles.length}`);
console.log("ROUTE COMPOSITION = PASS");
console.log("SEARCH ORCHESTRATION OWNER = SearchShell");
console.log("LIST + MAP = PASS");
console.log("FILTER DRAWER = PASS");
console.log("PREVIEW DOES NOT CLAIM VERIFIED = PASS");
console.log("NO STATE.JSON RUNTIME = PASS");
console.log("NO ACRL RUNTIME = PASS");
