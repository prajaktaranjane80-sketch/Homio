import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();

function read(relativePath) {
  const absolutePath = path.join(root, relativePath);

  assert.ok(
    fs.existsSync(absolutePath),
    `F12 required file is missing: ${relativePath}`,
  );

  return fs.readFileSync(absolutePath, "utf8");
}

const requiredFiles = [
  "src/features/f12_globalization/README.md",
  "src/features/f12_globalization/MarketSelector.tsx",
  "src/features/f12_globalization/MarketSelector.module.css",
  "src/features/f12_globalization/MarketActivationBadge.tsx",
  "src/features/f12_globalization/MarketStatus.tsx",
  "src/features/f12_globalization/MarketFeatureGate.tsx",
  "src/features/f12_globalization/MarketUnavailableState.tsx",
  "src/features/f12_globalization/MarketComingSoon.tsx",
  "src/features/f12_globalization/MarketAvailabilityNotice.tsx",
  "src/features/f12_globalization/MarketActivationWorkspace.tsx",
  "src/features/f12_globalization/MarketActivationWorkspace.module.css",
  "src/features/f12_globalization/CountrySelector.tsx",
  "src/features/f12_globalization/CitySelector.tsx",
  "src/features/f12_globalization/LocalitySelector.tsx",
  "src/features/f12_globalization/CurrencySelector.tsx",
  "src/features/f12_globalization/UnitSelector.tsx",
  "src/features/f12_globalization/LanguageSelector.tsx",
  "src/features/f12_globalization/MarketFieldSelectors.module.css",
  "src/features/f12_globalization/MarketStates.module.css",
  "src/features/f12_globalization/market-activation.types.ts",
  "src/features/f12_globalization/market-activation.constants.ts",
  "src/features/f12_globalization/market-activation.utils.ts",

  "src/components/system/SystemComponents.module.css",
  "src/components/system/MarketAvailabilityState.tsx",
  "src/components/system/ComingSoonState.tsx",
  "src/components/system/FeatureLockedState.tsx",
  "src/components/system/LoadingScreen.tsx",
  "src/components/system/SkeletonGrid.tsx",
  "src/components/system/EmptyResults.tsx",
  "src/components/system/ErrorRetry.tsx",
  "src/components/system/NoResults.tsx",
  "src/components/system/VerificationBadge.tsx",
  "src/components/system/InventorySourceBadge.tsx",
  "src/components/system/RecommendationBadge.tsx",
  "src/components/system/LastUpdated.tsx",
  "src/components/system/StatusBadge.tsx",
  "src/components/system/SaveButton.tsx",
  "src/components/system/CompareButton.tsx",
  "src/components/system/ShareButton.tsx",
  "src/components/system/EnquiryButton.tsx",
  "src/components/system/VisitButton.tsx",

  "src/components/navigation/GlobalMenus.module.css",
  "src/components/navigation/GlobalMegaMenu.tsx",
  "src/components/navigation/ExploreMenu.tsx",
  "src/components/navigation/MarketsMenu.tsx",
  "src/components/navigation/IntelligenceMenu.tsx",
  "src/components/navigation/ServicesMenu.tsx",
  "src/components/navigation/MyHomioMenu.tsx",
  "src/components/navigation/ProfessionalMenu.tsx",
  "src/components/navigation/GlobalMarketSwitcher.tsx",
  "src/components/navigation/MobileMegaMenu.tsx",

  "src/components/search/SearchExperience.types.ts",
  "src/components/search/SearchExperience.module.css",
  "src/components/search/SearchOverlay.tsx",
  "src/components/search/SearchAutocomplete.tsx",
  "src/components/search/SearchSuggestionGroup.tsx",
  "src/components/search/SearchRecentItem.tsx",
  "src/components/search/SearchPopularItem.tsx",
  "src/components/search/SearchLocationSuggestion.tsx",
  "src/components/search/SearchProjectSuggestion.tsx",
  "src/components/search/SearchPropertySuggestion.tsx",
  "src/components/search/SearchFilterSummary.tsx",
  "src/components/search/SearchActiveFilters.tsx",

  "src/features/content/ContentExperience.types.ts",
  "src/features/content/ContentExperience.module.css",
  "src/features/content/ContentCollection.tsx",
  "src/features/content/AdviceIndex.tsx",
  "src/features/content/AdviceCategory.tsx",
  "src/features/content/AdviceArticle.tsx",
  "src/features/content/AdviceTopicBar.tsx",
  "src/features/content/MarketReportIndex.tsx",
  "src/features/content/MarketReportDetail.tsx",
  "src/features/content/LocalityReport.tsx",
  "src/features/content/CityGuide.tsx",
  "src/features/content/FinanceGuide.tsx",
  "src/features/content/LegalGuide.tsx",
  "src/features/content/InvestmentInsight.tsx",
  "src/features/content/ProjectGuide.tsx",
  "src/features/content/PropertyVideo.tsx",
  "src/features/content/AIInsight.tsx",

  "src/features/post_property/post-property.types.ts",
  "src/features/post_property/PostProperty.module.css",
  "src/features/post_property/PostPropertyShell.tsx",
  "src/features/post_property/PostPropertyType.tsx",
  "src/features/post_property/PostPropertyLocation.tsx",
  "src/features/post_property/PostPropertyOwnership.tsx",
  "src/features/post_property/PostPropertyDetails.tsx",
  "src/features/post_property/PostPropertyMedia.tsx",
  "src/features/post_property/PostPropertyDocuments.tsx",
  "src/features/post_property/PostPropertyPricing.tsx",
  "src/features/post_property/PostPropertyAvailability.tsx",
  "src/features/post_property/PostPropertyReview.tsx",
  "src/features/post_property/PostPropertyVerification.tsx",
  "src/features/post_property/PostPropertySubmit.tsx",
  "src/features/post_property/PostPropertyStatus.tsx",
];

for (const file of requiredFiles) {
  read(file);
}

const constants = read("src/features/f12_globalization/market-activation.constants.ts");
const utility = read("src/features/f12_globalization/market-activation.utils.ts");
const workspace = read("src/features/f12_globalization/MarketActivationWorkspace.tsx");

assert.match(
  constants,
  /id:\s*"pune-in"[\s\S]*?activationState:\s*"ACTIVE"/,
  "Pune must remain the designated active market policy",
);

for (const marketId of [
  "dubai-ae",
  "singapore-sg",
  "tokyo-jp",
  "london-gb",
  "new-york-us",
]) {
  const start = constants.indexOf(`id: "${marketId}"`);
  assert.notEqual(start, -1, `Configured market is missing: ${marketId}`);

  const marketBlock = constants.slice(start, start + 650);
  assert.match(
    marketBlock,
    /activationState:\s*"BUILT"/,
    `${marketId} must remain built but not operational`,
  );
}

assert.match(
  utility,
  /return verifiedCapabilities\.includes\(capability\)/,
  "Capability display policy must require verified capability input",
);

assert.match(
  workspace,
  /MarketStatus/,
  "The market activation workspace must display service-readiness disclosure",
);

const runtimeFiles = requiredFiles.filter((file) => /\.(ts|tsx)$/.test(file));
const runtimeSources = runtimeFiles.map((file) => read(file)).join("\n");

assert.doesNotMatch(
  runtimeSources,
  /\bAUTONOMY_ENGINE\b|\bACRL\b|REOS_CONTROL_CENTER[\\/]+data[\\/]+state\.json/i,
  "Frontend runtime must not depend on ACRL or live Control Center state",
);

let cssImportsChecked = 0;
let styleReferencesChecked = 0;

for (const file of runtimeFiles.filter((item) => item.endsWith(".tsx"))) {
  const source = read(file);

  const imports = [
    ...source.matchAll(
      /import\s+(\w+)\s+from\s+["']([^"']+\.module\.css)["'];?/g,
    ),
  ];

  for (const match of imports) {
    const variable = match[1];
    const cssReference = match[2];
    const cssPath = path.resolve(path.dirname(path.join(root, file)), cssReference);
    const relativeCssPath = path.relative(root, cssPath).replaceAll("\\", "/");

    const css = read(relativeCssPath);
    cssImportsChecked += 1;

    const declaredClasses = new Set(
      [...css.matchAll(/\.([A-Za-z_][A-Za-z0-9_-]*)/g)].map(
        (item) => item[1],
      ),
    );

    const escapedVariable = variable.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const classPattern = new RegExp(
      `\\b${escapedVariable}\\.([A-Za-z_][A-Za-z0-9_]*)`,
      "g",
    );

    for (const classMatch of source.matchAll(classPattern)) {
      styleReferencesChecked += 1;

      assert.ok(
        declaredClasses.has(classMatch[1]),
        `${file} references missing CSS class ${classMatch[1]} in ${relativeCssPath}`,
      );
    }
  }
}

const packageJson = JSON.parse(read("package.json"));

assert.ok(
  packageJson.scripts["verify:f12"],
  "package.json must declare verify:f12",
);

assert.match(
  packageJson.scripts.verify,
  /npm run verify:f11 && npm run verify:f12/,
  "Full verification must run F12 after F11",
);

console.log(
  `F12 verification passed: ${requiredFiles.length} required files, ` +
    `${cssImportsChecked} CSS module imports, ` +
    `${styleReferencesChecked} CSS class references, market policy and runtime boundaries.`,
);
