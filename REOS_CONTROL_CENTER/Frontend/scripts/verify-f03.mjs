import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, "..");

const requiredFiles = [
  "src/app/search/page.tsx",
  "src/app/search/page.module.css",
  "src/features/f03_search/SearchShell.tsx",
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

const page = read("src/app/search/page.tsx");
const results = read("src/features/f03_search/SearchResults.tsx");
const drawer = read("src/features/f03_search/SearchFilterDrawer.tsx");

assert(
  page.includes("SearchResults"),
  "Search route is not wired to SearchResults.",
);

assert(
  page.includes("SearchFilterDrawer"),
  "Search route is not wired to SearchFilterDrawer.",
);

assert(
  results.includes("SearchListView") &&
    results.includes("SearchMapView"),
  "SearchResults does not expose both list and map modes.",
);

assert(
  drawer.includes("SearchAdvancedFilters"),
  "SearchFilterDrawer is not wired to SearchAdvancedFilters.",
);

for (const forbidden of forbiddenRuntimeReferences) {
  assert(
    !page.includes(forbidden),
    `Forbidden runtime reference found in search/page.tsx: ${forbidden}`,
  );

  assert(
    !results.includes(forbidden),
    `Forbidden runtime reference found in SearchResults.tsx: ${forbidden}`,
  );

  assert(
    !drawer.includes(forbidden),
    `Forbidden runtime reference found in SearchFilterDrawer.tsx: ${forbidden}`,
  );
}

console.log("F03 SEARCH INTEGRATION = PASS");
console.log(`FILES VERIFIED = ${requiredFiles.length}`);
console.log("SEARCH ROUTE = PASS");
console.log("LIST + MAP = PASS");
console.log("FILTER DRAWER = PASS");
console.log("NO STATE.JSON RUNTIME = PASS");
console.log("NO ACRL RUNTIME = PASS");
