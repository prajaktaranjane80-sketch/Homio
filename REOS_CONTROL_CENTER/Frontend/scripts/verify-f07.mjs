import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const featureRoot = "src/features/f07_my_homio/";

function assert(condition, message) {
  if (!condition) {
    throw new Error(`F07 verification failed: ${message}`);
  }
}

function read(relativePath) {
  const absolute = path.join(root, relativePath);

  assert(
    fs.existsSync(absolute),
    `Required file is missing: ${relativePath}`,
  );

  return fs.readFileSync(absolute, "utf8");
}

const requiredFiles = [
  "README.md",
  "MyHomioShell.tsx",
  "MyHomioDashboard.tsx",
  "MyHomioProfile.tsx",
  "MyHomioSaved.tsx",
  "MyHomioCompare.tsx",
  "MyHomioRecentSearches.tsx",
  "MyHomioRecentViews.tsx",
  "MyHomioEnquiries.tsx",
  "MyHomioConversations.tsx",
  "MyHomioVisits.tsx",
  "MyHomioRecommendations.tsx",
  "MyHomioBrokerageJourney.tsx",
  "MyHomioDocuments.tsx",
  "MyHomioNotifications.tsx",
  "MyHomioSettings.tsx",
  "my-homio.types.ts",
  "myHomioActivityStore.ts",
  "MyHomio.module.css",
];

const sources = new Map(
  requiredFiles.map((name) => [
    name,
    read(`${featureRoot}${name}`),
  ]),
);

const route = read("src/app/my/page.tsx");
const searchShell = read("src/features/f03_search/SearchShell.tsx");
const searchList = read("src/features/f03_search/SearchListView.tsx");
const searchMap = read("src/features/f03_search/SearchMapView.tsx");
const propertyActions = read("src/features/f04_property/PropertyActionBar.tsx");
const projectActions = read("src/features/f05_project/ProjectActions.tsx");
const f06Store = read("src/features/f06_save_compare/saveCompareSession.ts");
const packageJson = JSON.parse(read("package.json"));

assert(
  route.includes("readSessionCookie") &&
    route.includes("SESSION_COOKIE") &&
    route.includes('redirect("/login?returnTo=%2Fmy")') &&
    route.includes("MyHomioShell"),
  "The /my route must preserve server authentication and render F07.",
);

const shell = sources.get("MyHomioShell.tsx");

for (const component of [
  "MyHomioDashboard",
  "MyHomioProfilePage",
  "MyHomioSaved",
  "MyHomioCompare",
  "MyHomioRecentSearches",
  "MyHomioRecentViews",
  "MyHomioEnquiries",
  "MyHomioConversations",
  "MyHomioVisits",
  "MyHomioRecommendations",
  "MyHomioBrokerageJourney",
  "MyHomioDocuments",
  "MyHomioNotifications",
  "MyHomioSettings",
]) {
  assert(
    shell.includes(component),
    `My HOMIO navigation/composition is missing ${component}.`,
  );
}

assert(
  shell.includes("useSaveCompareSession") &&
    shell.includes("useMyHomioActivity") &&
    shell.includes('action="/api/auth/logout"'),
  "The shell must use the shared stores and the real sign-out endpoint.",
);

const activityStore = sources.get("myHomioActivityStore.ts");

assert(
  activityStore.includes("sessionStorage") &&
    activityStore.includes("recordRecentSearch") &&
    activityStore.includes("toggleSavedSearch") &&
    activityStore.includes("recordRecentView"),
  "The activity store must capture, validate and restore tab-session activity.",
);

assert(
  searchShell.includes("recordRecentSearch(searchDraft)") &&
    searchShell.includes("toggleSavedSearch(searchDraft)") &&
    searchShell.includes("useMyHomioActivity"),
  "Search must record real criteria and support saving/removing requirements.",
);

assert(
  searchList.includes("`${property.entityType}:${property.id}`"),
  "Search card selection must use entity-aware identity.",
);

assert(
  searchMap.includes("`${property.entityType}:${property.id}`"),
  "Search map-list selection must isolate property and project IDs.",
);

assert(
  propertyActions.includes("recordRecentView") &&
    propertyActions.includes('kind: "property"'),
  "Opening a property detail page must record its real detail view.",
);

assert(
  projectActions.includes("recordRecentView") &&
    projectActions.includes('kind: "project"'),
  "Opening a project detail page must record its real detail view.",
);

assert(
  sources.get("MyHomioSaved.tsx").includes("useSaveCompareSession") &&
    sources.get("MyHomioCompare.tsx").includes("useSaveCompareSession") &&
    sources.get("MyHomioCompare.tsx").includes("COMPARE_MAX_ITEMS") &&
    f06Store.includes("toggleComparedItem"),
  "F07 Save and Compare must reuse F06 rather than creating duplicate state.",
);

for (const name of [
  "MyHomioEnquiries.tsx",
  "MyHomioConversations.tsx",
  "MyHomioVisits.tsx",
  "MyHomioRecommendations.tsx",
  "MyHomioDocuments.tsx",
  "MyHomioNotifications.tsx",
]) {
  assert(
    sources.get(name).length > 100,
    `${name} must have a purpose-specific workspace view.`,
  );
}

assert(
  packageJson.scripts?.["verify:f07"] === "node ./scripts/verify-f07.mjs" &&
    packageJson.scripts?.verify?.includes("npm run verify:f07"),
  "F07 must be included in the full frontend verification workflow.",
);

for (const [name, source] of [
  ...[...sources.entries()].filter(([name]) => name !== "README.md"),
  ["protected /my route", route],
  ["Search integration", searchShell],
  ["Search list", searchList],
  ["Search map list", searchMap],
  ["Property view integration", propertyActions],
  ["Project view integration", projectActions],
]) {
  assert(
    !source.includes("AUTONOMY_ENGINE") &&
      !source.includes("data/state.json"),
    `Forbidden backend runtime coupling found in ${name}.`,
  );
}

console.log("F07 MY HOMIO CONTRACT = PASS");
console.log("PROTECTED AUTHENTICATED ROUTE = PASS");
console.log("SESSION ACTIVITY / SEARCH INTEGRATION = PASS");
console.log("ENTITY-AWARE SEARCH AND COMPARISON = PASS");
console.log("F06 SHARED STORE INTEGRATION = PASS");
console.log("NO FORBIDDEN BACKEND RUNTIME COUPLING = PASS");
console.log("F07 INCLUDED IN FULL VERIFY = PASS");
