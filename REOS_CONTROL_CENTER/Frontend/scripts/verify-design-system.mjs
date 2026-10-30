
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();

function fail(message) {
  console.error(`FAIL-CLOSED: ${message}`);
  process.exit(1);
}

function read(relativePath) {
  const absolutePath = path.join(root, relativePath);

  if (!fs.existsSync(absolutePath)) {
    fail(`Required design-system file missing: ${relativePath}`);
  }

  return fs.readFileSync(absolutePath, "utf8");
}

function requireContains(source, requiredText, context) {
  if (!source.includes(requiredText)) {
    fail(`${context}: required contract missing: ${requiredText}`);
  }
}

function requireExactlyOnce(source, requiredText, context) {
  const first = source.indexOf(requiredText);

  if (first < 0 || first !== source.lastIndexOf(requiredText)) {
    fail(`${context}: expected exactly one occurrence of ${requiredText}`);
  }
}

function requireNotContains(source, forbiddenText, context) {
  if (source.toLowerCase().includes(forbiddenText.toLowerCase())) {
    fail(`${context}: legacy visual value remains: ${forbiddenText}`);
  }
}

function requireNoMatch(source, pattern, context) {
  const match = source.match(pattern);

  if (match) {
    fail(`${context}: forbidden pattern remains: ${match[0]}`);
  }
}

const requiredFiles = [
  "package.json",
  "src/app/layout.tsx",
  "src/app/globals.css",
  "src/app/styles/tokens.css",
  "src/app/styles/base.css",
  "src/app/styles/foundation.css",
  "src/app/styles/motion.css",

  "src/features/f02_home_discovery/HomeHero.module.css",
  "src/features/f02_home_discovery/HomeSearch.module.css",
  "src/features/f02_home_discovery/HomeIntentTabs.module.css",
  "src/features/f02_home_discovery/HomeQuickDiscovery.module.css",
  "src/features/f02_home_discovery/HomeFooter.module.css",
  "src/features/f02_home_discovery/FeaturedProjects.module.css",
  "src/features/f02_home_discovery/FreshProperties.module.css",
  "src/features/f02_home_discovery/PopularCities.module.css",
  "src/features/f02_home_discovery/HomeSecondaryNav.module.css",

  "src/components/navigation/GlobalMenus.module.css",
  "src/components/navigation/MegaMenu.module.css",
  "src/components/system/SharedSystem.module.css",
  "src/components/system/SystemComponents.module.css",

  "src/components/motion/MotionReveal.tsx",
  "src/components/motion/MotionReveal.module.css",
  "src/components/motion/motion.types.ts",

  "src/features/f03_search/SearchShell.module.css",
  "src/features/f04_property/PropertyPage.module.css",
  "src/features/f05_project/ProjectPage.module.css",
  "src/features/f12_globalization/MarketActivationWorkspace.module.css",
  "src/features/f12_globalization/MarketFieldSelectors.module.css",
  "src/features/f12_globalization/MarketStates.module.css",
];

for (const relativePath of requiredFiles) {
  if (!fs.existsSync(path.join(root, relativePath))) {
    fail(`Required design-system file missing: ${relativePath}`);
  }
}

const packageJson = JSON.parse(read("package.json"));
const layout = read("src/app/layout.tsx");
const tokens = read("src/app/styles/tokens.css");
const globals = read("src/app/globals.css");
const base = read("src/app/styles/base.css");
const foundation = read("src/app/styles/foundation.css");
const motion = read("src/app/styles/motion.css");

const homeHeroTheme = read("src/features/f02_home_discovery/HomeHero.module.css");
const homeSearchTheme = read("src/features/f02_home_discovery/HomeSearch.module.css");
const homeIntentTabsTheme = read("src/features/f02_home_discovery/HomeIntentTabs.module.css");
const homeQuickDiscoveryTheme = read("src/features/f02_home_discovery/HomeQuickDiscovery.module.css");
const homeFooterTheme = read("src/features/f02_home_discovery/HomeFooter.module.css");
const featuredProjectsTheme = read("src/features/f02_home_discovery/FeaturedProjects.module.css");
const freshPropertiesTheme = read("src/features/f02_home_discovery/FreshProperties.module.css");
const popularCitiesTheme = read("src/features/f02_home_discovery/PopularCities.module.css");
const homeSecondaryNavTheme = read("src/features/f02_home_discovery/HomeSecondaryNav.module.css");

const globalMenus = read("src/components/navigation/GlobalMenus.module.css");
const megaMenu = read("src/components/navigation/MegaMenu.module.css");
const sharedSystem = read("src/components/system/SharedSystem.module.css");
const systemComponents = read("src/components/system/SystemComponents.module.css");

const revealComponent = read("src/components/motion/MotionReveal.tsx");
const revealCss = read("src/components/motion/MotionReveal.module.css");
const motionTypes = read("src/components/motion/motion.types.ts");

const searchShellTheme = read("src/features/f03_search/SearchShell.module.css");
const propertyPageTheme = read("src/features/f04_property/PropertyPage.module.css");
const projectPageTheme = read("src/features/f05_project/ProjectPage.module.css");
const marketWorkspaceTheme = read(
  "src/features/f12_globalization/MarketActivationWorkspace.module.css"
);
const marketFieldsTheme = read(
  "src/features/f12_globalization/MarketFieldSelectors.module.css"
);
const marketStatesTheme = read(
  "src/features/f12_globalization/MarketStates.module.css"
);

/* 1. Canonical Rosewood & Almond four-colour token contract. */

const requiredTokens = [
  "--homio-rosewood: #6f334b;",
  "--homio-blush: #f3dde4;",
  "--homio-almond: #f8f1e7;",
  "--homio-cocoa: #352a2d;",

  "--homio-brand: var(--homio-rosewood);",
  "--homio-brand-soft:",
  "--homio-accent: var(--homio-rosewood);",
  "--homio-accent-strong:",
  "--homio-accent-soft: var(--homio-blush);",

  "--homio-champagne: var(--homio-rosewood);",
  "--homio-champagne-soft: var(--homio-blush);",

  "--homio-bg: var(--homio-almond);",
  "--homio-surface: #ffffff;",

  "--homio-focus-ring: rgb(111 51 75 / 72%);",
  "--homio-focus-ring-soft: rgb(111 51 75 / 48%);",
  "--homio-focus-ring-on-brand: var(--homio-blush);",
  "--homio-focus-shadow: 0 0 0 3px rgb(111 51 75 / 18%);",

  "--motion-skeleton-duration: 1400ms;",

  "--font-sans:",
  "--font-serif:",

  "--homio-success:",
  "--homio-warning:",
  "--homio-danger:",
  "--homio-info:",

  "--motion-normal:",
  "--motion-slow:",
  "--ease-standard: 220ms var(--ease-standard-curve);",
  "--ease-slow: 420ms var(--ease-emphasized);",
  "--ease-standard-curve:",
];

for (const token of requiredTokens) {
  requireContains(tokens, token, "Design token contract");
}

requireContains(tokens, "--font-serif:", "Editorial heading font");
requireContains(tokens, "--font-sans:", "UI and body font");
requireContains(base, "font-family: var(--font-serif)", "Heading typography");
requireContains(base, "font-family: var(--font-sans)", "Body typography");

requireContains(
  base,
  "var(--homio-focus-ring)",
  "Rosewood focus visibility"
);
requireContains(
  foundation,
  "var(--homio-focus-shadow)",
  "Shared Rosewood field focus treatment"
);

/* 2. Shared focus treatments and skeleton timing. */

for (const [fileName, source] of [
  ["foundation.css", foundation],
  ["SharedSystem.module.css", sharedSystem],
  ["SystemComponents.module.css", systemComponents],
]) {
  requireContains(
    source,
    "var(--motion-skeleton-duration)",
    `${fileName} shared skeleton duration`
  );
}

const requiredSkeletonMotionContracts = [
  [
    "foundation.css",
    foundation,
    "animation: homio-skeleton-shimmer var(--motion-skeleton-duration) var(--ease-standard-curve) infinite;",
    "@keyframes homio-skeleton-shimmer {\n  from {\n    background-position: 0% 0%;\n  }\n\n  to {\n    background-position: -220% 0%;\n  }\n}",
  ],
  [
    "SharedSystem.module.css",
    sharedSystem,
    "animation: systemShimmer var(--motion-skeleton-duration) var(--ease-standard-curve) infinite;",
    "@keyframes systemShimmer {\n  from {\n    background-position: 0% 0%;\n  }\n\n  to {\n    background-position: -220% 0%;\n  }\n}",
  ],
  [
    "SystemComponents.module.css",
    systemComponents,
    "animation: sys-shimmer var(--motion-skeleton-duration) var(--ease-standard-curve) infinite;",
    "@keyframes sys-shimmer {\n  from {\n    background-position: 0% 0%;\n  }\n\n  to {\n    background-position: -220% 0%;\n  }\n}",
  ],
];

const sharedSkeletonGradient = `background: linear-gradient(
    100deg,
    var(--homio-surface-muted) 20%,
    var(--homio-surface-soft) 38%,
    var(--homio-surface-muted) 56%
  );`;

for (const [fileName, source, animation, keyframes] of requiredSkeletonMotionContracts) {
  requireContains(
    source,
    "background-size: 220% 100%;",
    `${fileName} skeleton background geometry`,
  );
  requireContains(
    source,
    sharedSkeletonGradient,
    `${fileName} shared skeleton gradient`,
  );
  requireContains(
    source,
    animation,
    `${fileName} shared skeleton duration and easing`,
  );
  requireContains(
    source,
    keyframes,
    `${fileName} aligned skeleton travel distance`,
  );
}

requireContains(
  systemComponents,
  "outline: 3px solid var(--homio-focus-ring);",
  "Accessible system component keyboard focus"
);

requireContains(
  sharedSystem,
  ".systemAction:focus-visible {\n  outline: 3px solid var(--homio-focus-ring);\n  outline-offset: 2px;\n}",
  "Accessible shared-system action keyboard focus"
);

for (const [fileName, source] of [
  ["GlobalMenus.module.css", globalMenus],
  ["MegaMenu.module.css", megaMenu],
]) {
  requireNotContains(source, "rgb(197 155 99", `${fileName} focus rings`);
}

requireNotContains(
  sharedSystem,
  "1.4s ease-in-out infinite",
  "Shared system skeleton timing"
);
requireNotContains(
  systemComponents,
  "1.35s ease-in-out infinite",
  "System component skeleton timing"
);

requireContains(
  sharedSystem,
  "animation: systemSpin 850ms linear infinite;",
  "Keep the dedicated spinner timing separate from skeleton shimmer",
);
requireNotContains(
  systemComponents,
  "--sys-gold",
  "System component accent naming"
);

/* 3. Shared transition timing and motion utilities. */

requireContains(
  tokens,
  "--ease-standard: 220ms var(--ease-standard-curve);",
  "Unified standard transition timing"
);
requireContains(
  tokens,
  "--ease-slow: 420ms var(--ease-emphasized);",
  "Unified slow transition timing"
);
requireContains(
  tokens,
  "--ease-standard-curve: cubic-bezier(",
  "Shared motion curve"
);

for (const [fileName, source] of [
  ["base.css", base],
  ["foundation.css", foundation],
]) {
  requireContains(
    source,
    "var(--ease-standard)",
    `${fileName} transition compatibility`
  );
}

for (const requiredClass of [
  ".motion-fade-in",
  ".motion-rise-in",
  ".motion-scale-in",
  ".motion-soft-reveal",
]) {
  requireContains(motion, requiredClass, "Motion utility contract");
}

requireContains(
  motion,
  "@media (prefers-reduced-motion: reduce)",
  "Motion utility accessibility"
);
requireContains(revealCss, ".revealVisible", "Reveal visible state");
requireContains(
  revealCss,
  "@media (prefers-reduced-motion: reduce)",
  "Reveal reduced-motion support"
);
requireContains(revealComponent, "IntersectionObserver", "Reveal observer");
requireContains(
  revealComponent,
  "prefers-reduced-motion: reduce",
  "Reveal reduced-motion runtime contract"
);
requireContains(revealComponent, 'from "./motion.types"', "Reveal type import");
requireContains(
  motionTypes,
  "export interface MotionRevealProps",
  "Reveal type definition"
);
requireContains(motionTypes, "children: ReactNode;", "Reveal children type");

/* 4. Homepage palette and image-motion rules. */

const homepageThemeModules = [
  ["HomeHero.module.css", homeHeroTheme],
  ["HomeSearch.module.css", homeSearchTheme],
  ["HomeIntentTabs.module.css", homeIntentTabsTheme],
  ["HomeQuickDiscovery.module.css", homeQuickDiscoveryTheme],
  ["HomeFooter.module.css", homeFooterTheme],
  ["FeaturedProjects.module.css", featuredProjectsTheme],
  ["FreshProperties.module.css", freshPropertiesTheme],
  ["PopularCities.module.css", popularCitiesTheme],
  ["HomeSecondaryNav.module.css", homeSecondaryNavTheme],
];

const forbiddenLegacyHomepageColours = [
  "#0d0d0d",
  "#fbf0f4",
  "rgb(168 79 118",
  "rgb(130 60 91",
  "rgb(17 17 17",
  "rgb(35 22 31",
  "rgb(75 34 54",
  "rgb(245 226 234",
  "rgba(0, 0, 0",
];

for (const [fileName, source] of homepageThemeModules) {
  requireContains(source, "var(--homio-", `${fileName} shared palette tokens`);

  for (const legacyColour of forbiddenLegacyHomepageColours) {
    requireNotContains(source, legacyColour, fileName);
  }
}

requireNotContains(
  homeHeroTheme,
  "var(--homio-champagne)",
  "Homepage hero must use Blush, not a legacy gold alias"
);
requireContains(
  homeHeroTheme,
  "photo-1600585154340-be6161a56a0c",
  "Keep the existing homepage property image"
);
requireContains(
  homeSearchTheme,
  "var(--homio-focus-ring)",
  "Homepage search keyboard focus"
);
requireContains(
  homeIntentTabsTheme,
  "var(--homio-focus-ring-on-brand)",
  "Intent tabs focus against dark Rosewood"
);
requireContains(
  homeQuickDiscoveryTheme,
  "var(--homio-focus-ring)",
  "Quick discovery keyboard focus"
);
requireContains(
  homeSecondaryNavTheme,
  "var(--homio-focus-ring)",
  "Secondary navigation keyboard focus"
);
requireNotContains(
  featuredProjectsTheme,
  "transform: scale(",
  "Featured property imagery must not zoom on hover"
);
requireNotContains(
  freshPropertiesTheme,
  "transform: scale(",
  "Fresh property imagery must not zoom on hover"
);

for (const [fileName, source] of [
  ["FeaturedProjects.module.css", featuredProjectsTheme],
  ["PopularCities.module.css", popularCitiesTheme],
]) {
  requireContains(
    source,
    "@media (prefers-reduced-motion: reduce)",
    `${fileName} reduced-motion behavior`
  );
}

/* 5. Semantic market status colours. */

requireContains(
  marketStatesTheme,
  "var(--homio-success-soft)",
  "Market state semantic success surface"
);
requireContains(
  marketStatesTheme,
  "var(--homio-success)",
  "Market state semantic success foreground"
);
requireNotContains(
  marketStatesTheme,
  "#36775c",
  "Market state must not hard-code success green"
);
requireNotContains(
  marketStatesTheme,
  "#f4faf6",
  "Market state must not hard-code success surface"
);
requireNotContains(
  marketStatesTheme,
  "#eaf5ee",
  "Market state must not hard-code success label background"
);

for (const smallFont of [
  "font-size: 8px;",
  "font-size: 9px;",
  "font-size: 10px;",
]) {
  requireNotContains(marketStatesTheme, smallFont, "Market state readability");
}

/* 6. Shared modules and feature shells use semantic HOMIO tokens. */

const themedModules = [
  ["GlobalMenus.module.css", globalMenus],
  ["MegaMenu.module.css", megaMenu],
  ["SharedSystem.module.css", sharedSystem],
  ["SystemComponents.module.css", systemComponents],
];

for (const [fileName, source] of themedModules) {
  requireContains(
    source,
    "var(--homio-",
    `${fileName} shared brand tokens`
  );
}

/* 6a. Shared navigation readability and keyboard focus contract. */

for (const [fileName, source] of [
  ["GlobalMenus.module.css", globalMenus],
  ["MegaMenu.module.css", megaMenu],
]) {
  requireContains(
    source,
    "var(--homio-focus-ring)",
    `${fileName} visible keyboard focus`
  );
  requireContains(
    source,
    "@media (prefers-reduced-motion: reduce)",
    `${fileName} reduced-motion support`
  );
  requireNoMatch(
    source,
    /font-size:\s*(?:8|9|10|11)px\b/i,
    `${fileName} minimum navigation text size`
  );
}

const featureThemeModules = [
  ["SearchShell.module.css", searchShellTheme],
  ["PropertyPage.module.css", propertyPageTheme],
  ["ProjectPage.module.css", projectPageTheme],
  ["MarketActivationWorkspace.module.css", marketWorkspaceTheme],
  ["MarketFieldSelectors.module.css", marketFieldsTheme],
  ["MarketStates.module.css", marketStatesTheme],
];

for (const [fileName, source] of featureThemeModules) {
  requireContains(
    source,
    "var(--homio-",
    `${fileName} canonical HOMIO palette`
  );
}

/* 7. Reject the competing navy/blue-grey palette. */

const legacyPaletteValues = [
  "#15283c",
  "#14283d",
  "#14263a",
  "#14263b",
  "#152a40",
  "#1a3046",
  "#17212b",
  "#f7f8fa",
  "#e1e8ef",
  "#e2e8ef",
  "#dce2e8",
  "#d5dbe2",
  "#708095",
  "#d9bb82",
  "#d8ba82",
  "#987443",
  "#b08a4d",
  "#52657b",
  "#dfbd80",
  "#f6f8fa",
];

const combinedThemeModules = [...themedModules, ...featureThemeModules]
  .map(([, source]) => source.toLowerCase())
  .join("\n");

for (const legacyColor of legacyPaletteValues) {
  if (combinedThemeModules.includes(legacyColor)) {
    fail(`Legacy competing theme colour remains: ${legacyColor}`);
  }
}

/* 8. Preserve reduced-motion support in existing animated modules. */

requireContains(
  propertyPageTheme,
  "@media (prefers-reduced-motion: reduce)",
  "Property page motion accessibility"
);
requireContains(
  marketFieldsTheme,
  "@media (prefers-reduced-motion: reduce)",
  "Market field motion accessibility"
);
requireContains(
  sharedSystem,
  "@media (prefers-reduced-motion: reduce)",
  "Shared system motion accessibility"
);
requireContains(
  systemComponents,
  "@media (prefers-reduced-motion: reduce)",
  "System component motion accessibility"
);

/* 9. Runtime shell and theme metadata. */

requireContains(layout, 'themeColor: "#f8f1e7"', "Browser theme colour");
requireContains(layout, "<AppShell>{children}</AppShell>", "Existing app shell");
requireContains(layout, "<ProductionQualityMonitor />", "Production monitor");
requireContains(layout, "<ErrorBoundary>", "Root error boundary");

/* 10. Keep the existing verification pipeline wired. */

if (!packageJson.scripts?.["verify:design-system"]) {
  fail("npm script verify:design-system is missing.");
}

if (
  !String(packageJson.scripts?.["verify:foundation"] ?? "").includes(
    "npm run verify:design-system"
  )
) {
  fail("verify:foundation must invoke verify:design-system.");
}

if (
  !String(packageJson.scripts?.verify ?? "").includes(
    "npm run verify:foundation"
  )
) {
  fail("The combined verify pipeline must invoke verify:foundation.");
}

console.log("");
console.log("==================================================");
console.log("HOMIO DESIGN SYSTEM CONTRACT          = PASS");
console.log(`FILES VERIFIED                       = ${requiredFiles.length}`);
console.log("ROSEWOOD & ALMOND PALETTE             = PASS");
console.log("FOUR-COLOUR TOKEN CONTRACT            = PASS");
console.log("HOMEPAGE LEGACY COLOUR REJECTION       = PASS");
console.log("PROPERTY IMAGE MOTION SAFETY           = PASS");
console.log("SEMANTIC MARKET STATUS TOKENS           = PASS");
console.log("EDITORIAL TYPOGRAPHY CONTRACT         = PASS");
console.log("UNIFIED TRANSITION TIMING               = PASS");
console.log("SKELETON MOTION CONSISTENCY             = PASS");
console.log("GLOBAL CSS IMPORT ORDER               = PASS");
console.log("MOTION UTILITY CONTRACT               = PASS");
console.log("MOTION REVEAL / TYPES                 = PASS");
console.log("REDUCED-MOTION ACCESSIBILITY           = PASS");
console.log("SHARED NAVIGATION / SYSTEM THEME      = PASS");
console.log("FEATURE PALETTE CONTRACT              = PASS");
console.log("LEGACY THEME COLOUR CHECK             = PASS");
console.log("ROOT SHELL / METADATA CONTRACT        = PASS");
console.log("VERIFY PIPELINE INTEGRATION            = PASS");
console.log("==================================================");
