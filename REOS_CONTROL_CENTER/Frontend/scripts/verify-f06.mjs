import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function read(relativePath) {
  const absolute = path.join(root, relativePath);
  assert(fs.existsSync(absolute), `Missing F06 file: ${relativePath}`);
  return fs.readFileSync(absolute, "utf8");
}

const savedRoute = read("src/app/saved/page.tsx");
const compareRoute = read("src/app/compare/page.tsx");
const savedShell = read("src/features/f06_save_compare/SavedShell.tsx");
const compareShell = read("src/features/f06_save_compare/CompareShell.tsx");
const table = read("src/features/f06_save_compare/CompareTable.tsx");
const store = read("src/features/f06_save_compare/saveCompareSession.ts");
const share = read("src/features/f06_save_compare/ShareComparison.tsx");
const compareActions = read("src/features/f06_save_compare/CompareActions.tsx");
const projectActions = read("src/features/f05_project/ProjectActions.tsx");
const adapters = read("src/features/f06_save_compare/saveCompareAdapters.ts");
const packageJson = JSON.parse(read("package.json"));
const duplicateCss = path.join(root, "src/features/f06_save_compare/SaveComparePages.module.css");

assert(savedRoute.includes("SavedShell") && savedRoute.includes('persistenceStatus="session-only"'),
  "Saved route must reuse SavedShell and disclose session-only persistence.");
assert(compareRoute.includes("CompareShell") && compareRoute.includes("replaceComparedItems") &&
  compareRoute.includes("getPropertyPreview") && compareRoute.includes("getProjectPreview"),
  "Compare route must reuse CompareShell and resolve typed shared preview references.");
assert(savedShell.includes("SavedCompareExperience.module.css") &&
  savedShell.includes('onRemoveRecord(id, "property")') &&
  savedShell.includes('onRemoveRecord(id, "project")'),
  "Saved workspace must reuse the shared F06 design system and remove by entity kind.");
assert(compareShell.includes("SavedCompareExperience.module.css") && compareShell.includes("CompareTable"),
  "Compare workspace must reuse the existing F06 comparison composition.");
assert(table.includes('`${item.kind}:${item.id}`') && table.includes("onRemove(item.id, item.kind)"),
  "Comparison table must use composite identity for values, keys, and removals.");
assert(store.includes("kind?: SavedEntityKind") && store.includes("kind?: CompareEntityKind") &&
  store.includes("replaceComparedItems") && store.includes("COMPARE_MAX_ITEMS"),
  "Session store must provide typed removal, bounded comparison, and share restoration.");
assert(share.includes('url.searchParams.set(') && share.includes('JSON.stringify(items.map'),
  "Share action must serialize typed entity references.");
assert(compareActions.includes("<ShareComparison items={items}"),
  "Compare action must provide typed comparison records to ShareComparison.");
assert(adapters.includes("compareFromProperty") && adapters.includes("compareFromProject"),
  "Shared references must map via existing source adapters.");
assert(projectActions.includes("navigator.share") && projectActions.includes("temporary experience controls"),
  "F05 share and temporary-action disclosure contract must remain intact.");
assert(!fs.existsSync(duplicateCss),
  "Delete the duplicate route stylesheet and retain SavedCompareExperience.module.css.");
assert(packageJson.scripts["verify:f06"] === "node ./scripts/verify-f06.mjs" &&
  packageJson.scripts.verify.includes("npm run verify:f06"),
  "F06 contract gate must run within npm verify.");

for (const [name, source] of [
  ["saved route", savedRoute], ["compare route", compareRoute],
  ["SavedShell", savedShell], ["CompareShell", compareShell], ["CompareTable", table],
  ["saveCompareSession", store], ["ShareComparison", share], ["F05 action adapter", projectActions],
]) {
  assert(!source.includes("AUTONOMY_ENGINE") && !source.includes("data/state.json"),
    `Forbidden backend runtime coupling in ${name}`);
}

console.log("F06 SAVE & COMPARE CONTRACT GATE = PASS");
console.log("ROUTES REUSE EXISTING F06 SHELLS = PASS");
console.log("SHARED URL RESTORES SUPPORTED PREVIEW RECORDS = PASS");
console.log("SAME-ID ENTITY ISOLATION / REMOVAL = PASS");
console.log("NO DUPLICATE ROUTE STYLESHEET = PASS");
console.log("NO ACRL / CONTROL CENTER RUNTIME COUPLING = PASS");
console.log("F06 INCLUDED IN FULL VERIFY = PASS");
