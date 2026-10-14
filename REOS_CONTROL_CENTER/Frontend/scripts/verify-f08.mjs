import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const featureRoot = "src/features/f08_ai/";

function assert(condition, message) {
  if (!condition) {
    throw new Error(`F08 verification failed: ${message}`);
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
  "AIWorkspace.tsx",
  "AISearch.tsx",
  "AINaturalLanguageInput.tsx",
  "AISuggestionPanel.tsx",
  "AIRecommendations.tsx",
  "AIBudgetGuidance.tsx",
  "AIPropertyComparison.tsx",
  "AILocalityComparison.tsx",
  "AIInvestmentAssistant.tsx",
  "AIRentalAssistant.tsx",
  "AIMarketAssistant.tsx",
  "AIPropertySummary.tsx",
  "AIConversationPreview.tsx",
  "AIBrokerageHandoff.tsx",
  "AIEmptyState.tsx",
  "AIErrorState.tsx",
  "ai.types.ts",
  "ai.constants.ts",
  "AIWorkspace.module.css",
];

const sources = new Map(
  requiredFiles.map((name) => [
    name,
    read(`${featureRoot}${name}`),
  ]),
);

const route = read("src/app/ai/page.tsx");
const navigation = read("src/components/shell/ResponsiveNavigation.tsx");
const compareStore = read(
  "src/features/f06_save_compare/saveCompareSession.ts",
);
const searchTypes = read("src/features/f03_search/search.types.ts");
const packageJson = JSON.parse(read("package.json"));
const workspace = sources.get("AIWorkspace.tsx");

for (const component of [
  "AISearch",
  "AINaturalLanguageInput",
  "AISuggestionPanel",
  "AIRecommendations",
  "AIBudgetGuidance",
  "AIPropertyComparison",
  "AILocalityComparison",
  "AIInvestmentAssistant",
  "AIRentalAssistant",
  "AIMarketAssistant",
  "AIPropertySummary",
  "AIConversationPreview",
  "AIBrokerageHandoff",
  "AIErrorState",
]) {
  assert(
    workspace.includes(component),
    `AIWorkspace is missing ${component}.`,
  );
}

assert(
  route.includes("AIWorkspace"),
  "The /ai route must render AIWorkspace.",
);

assert(
  navigation.includes('label: "HOMIO AI"') &&
    navigation.includes('href: "/ai"'),
  "Primary navigation must expose HOMIO AI.",
);

assert(
  packageJson.scripts?.["verify:f08"] ===
    "node ./scripts/verify-f08.mjs" &&
    packageJson.scripts?.verify?.includes("npm run verify:f08"),
  "F08 must be included in full verification.",
);

assert(
  sources.get("ai.constants.ts").includes(
    "AI_LIVE_SERVICE_CONNECTED = false",
  ),
  "F08 must disclose that no live AI service is connected.",
);

assert(
  workspace.includes("not connected") &&
    workspace.includes("does not fabricate"),
  "The workspace must clearly disclose service limits.",
);

assert(
  sources.get("AIPropertyComparison.tsx").includes(
    "useSaveCompareSession",
  ) &&
    sources.get("AIPropertyComparison.tsx").includes('href="/compare"') &&
    compareStore.includes("useSyncExternalStore"),
  "F08 must reuse the existing F06 compare store and route.",
);

assert(
  sources.get("ai.constants.ts").includes(
    'params.set("maxBudget", budget)',
  ) &&
    sources.get("ai.constants.ts").includes(
      'params.set("budgetCurrency", input.currency)',
    ) &&
    searchTypes.includes('type SearchIntent'),
  "Search handoff must use current F03 parameter conventions.",
);

assert(
  sources.get("AIErrorState.tsx").includes('role="alert"') &&
    sources.get("AIConversationPreview.tsx").includes(
      'aria-live="polite"',
    ),
  "Error and conversation updates must be accessible.",
);

for (const [name, source] of sources) {
  if (name === "README.md") {
    continue;
  }

  assert(
    !source.includes("AUTONOMY_ENGINE") &&
      !source.includes("data/state.json"),
    `Forbidden backend runtime coupling found in ${name}.`,
  );
}

for (const [name, source] of [
  ["AI route", route],
  ["AI navigation", navigation],
]) {
  assert(
    !source.includes("AUTONOMY_ENGINE") &&
      !source.includes("data/state.json"),
    `Forbidden backend runtime coupling found in ${name}.`,
  );
}

console.log("F08 HOMIO AI CONTRACT = PASS");
console.log("REQUIRED MODULES AND RESPONSIVE STYLES = PASS");
console.log("/ai ROUTE AND PRIMARY NAVIGATION = PASS");
console.log("F03 SEARCH HANDOFF = PASS");
console.log("F06 COMPARE STORE REUSE = PASS");
console.log("AI SERVICE LIMITATIONS DISCLOSED = PASS");
console.log("ACCESSIBLE ERROR AND UPDATE STATES = PASS");
console.log("NO FORBIDDEN BACKEND RUNTIME COUPLING = PASS");
console.log("F08 INCLUDED IN FULL VERIFY = PASS");
