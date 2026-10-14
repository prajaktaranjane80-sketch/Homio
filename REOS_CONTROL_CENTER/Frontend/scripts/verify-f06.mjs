import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function read(relativePath) {
  const absolute = path.join(root, relativePath);

  assert(
    fs.existsSync(absolute),
    `Missing F06 file: ${relativePath}`,
  );

  return fs.readFileSync(absolute, "utf8");
}

const savedRoute = read("src/app/saved/page.tsx");
const compareRoute = read("src/app/compare/page.tsx");

const savedShell = read(
  "src/features/f06_save_compare/SavedShell.tsx",
);
const compareShell = read(
  "src/features/f06_save_compare/CompareShell.tsx",
);
const table = read(
  "src/features/f06_save_compare/CompareTable.tsx",
);
const store = read(
  "src/features/f06_save_compare/saveCompareSession.ts",
);
const share = read(
  "src/features/f06_save_compare/ShareComparison.tsx",
);
const compareActions = read(
  "src/features/f06_save_compare/CompareActions.tsx",
);
const projectActions = read(
  "src/features/f05_project/ProjectActions.tsx",
);
const adapters = read(
  "src/features/f06_save_compare/saveCompareAdapters.ts",
);
const readme = read(
  "src/features/f06_save_compare/README.md",
);
const packageJson = JSON.parse(read("package.json"));

const duplicateCss = path.join(
  root,
  "src/features/f06_save_compare/SaveComparePages.module.css",
);

assert(
  savedRoute.includes("SavedShell") &&
    savedRoute.includes('persistenceStatus="session-only"') &&
    savedRoute.includes("removeSavedRecord"),
  "Saved route must reuse SavedShell and disclose session-only state.",
);

assert(
  compareRoute.includes("CompareShell") &&
    compareRoute.includes("useSaveCompareSession") &&
    compareRoute.includes("removeComparedItem") &&
    compareRoute.includes("clearComparedItems"),
  "Compare route must use the shared shell and typed session actions.",
);

assert(
  savedShell.includes("SavedCompareExperience.module.css") &&
    savedShell.includes('onRemoveRecord(id, "property")') &&
    savedShell.includes('onRemoveRecord(id, "project")') &&
    savedShell.includes('onRemoveRecord(id, "locality")'),
  "Saved workspace must use shared styling and remove by entity kind.",
);

assert(
  compareShell.includes("SavedCompareExperience.module.css") &&
    compareShell.includes("CompareTable") &&
    compareShell.includes("COMPARE_MAX_ITEMS"),
  "Compare workspace must reuse the existing comparison composition.",
);

assert(
  table.includes("`${item.kind}:${item.id}`") &&
    table.includes("onRemove(item.id, item.kind)"),
  "Comparison rows, keys and removals must use entity-aware identity.",
);

assert(
  store.includes("kind?: SavedEntityKind") &&
    store.includes("kind?: CompareEntityKind") &&
    store.includes("MAX_COMPARE_ITEMS = 4") &&
    store.includes(
      "snapshot.comparedItems.length >= MAX_COMPARE_ITEMS",
    ),
  "Session store must support typed removals and a four-item limit.",
);

assert(
  share.includes("url.searchParams.set(") &&
    share.includes('identities.join(",")') &&
    share.includes("will not automatically load in another browser"),
  "Share action must accurately disclose its session-only limitation.",
);

assert(
  compareActions.includes("ShareComparison") &&
    compareActions.includes("items={items}"),
  "Compare actions must pass typed items to the share control.",
);

assert(
  adapters.includes("compareFromSearchResult") &&
    adapters.includes("compareFromProperty") &&
    adapters.includes("compareFromProject"),
  "Search, Property and Project adapters must remain connected.",
);

assert(
  projectActions.includes("navigator.share") &&
    projectActions.includes("temporary experience controls"),
  "F05 sharing and temporary-action disclosure must remain intact.",
);

assert(
  readme.includes("A copied URL does not restore records in a separate browser.") &&
    readme.includes("A full page reload clears the store."),
  "Documentation must disclose the actual session-only behavior.",
);

assert(
  !fs.existsSync(duplicateCss),
  "Delete SaveComparePages.module.css; keep the shared F06 stylesheet.",
);

assert(
  packageJson.scripts["verify:f06"] ===
    "node ./scripts/verify-f06.mjs" &&
    packageJson.scripts.verify.includes("npm run verify:f06"),
  "F06 verification must remain included in npm verify.",
);

for (const [name, source] of [
  ["saved route", savedRoute],
  ["compare route", compareRoute],
  ["SavedShell", savedShell],
  ["CompareShell", compareShell],
  ["CompareTable", table],
  ["session store", store],
  ["share action", share],
  ["F05 actions", projectActions],
]) {
  assert(
    !source.includes("AUTONOMY_ENGINE") &&
      !source.includes("data/state.json"),
    `Forbidden backend runtime coupling in ${name}.`,
  );
}

console.log("F06 SAVE & COMPARE CONTRACT GATE = PASS");
console.log("EXISTING SHELLS AND ROUTES = PASS");
console.log("ENTITY-AWARE COMPARISON IDENTITY = PASS");
console.log("SESSION-ONLY DISCLOSURE = PASS");
console.log("FOUR-ITEM COMPARE LIMIT = PASS");
console.log("NO DUPLICATE ROUTE STYLESHEET = PASS");
console.log("NO FORBIDDEN BACKEND RUNTIME COUPLING = PASS");
console.log("F06 INCLUDED IN FULL VERIFY = PASS");
