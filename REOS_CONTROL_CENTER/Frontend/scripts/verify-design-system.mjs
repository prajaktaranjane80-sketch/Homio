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

const requiredFiles = [
  "package.json",
  "src/app/layout.tsx",
  "src/app/globals.css",
  "src/app/styles/tokens.css",
  "src/app/styles/base.css",
  "src/app/styles/foundation.css",
  "src/app/styles/motion.css",
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

/* 1. HOMIO premium blush/berry/champagne token contract */

const requiredTokens = [
  "--homio-brand: #111111;",
  "--homio-brand-soft: #292126;",
  "--homio-accent: #a84f76;",
  "--homio-accent-strong: #823c5b;",
  "--homio-accent-soft: #f5e2ea;",
  "--homio-champagne: #c59b63;",
  "--homio-champagne-soft: #f4ebdd;",
  "--homio-bg: #f8f7f4;",
  "--homio-surface: #ffffff;",
  "--homio-surface-soft: #fbf0f4;",
  "--font-sans:",
  "--font-serif:",
  "--homio-success:",
  "--homio-warning:",
  "--homio-danger:",
  "--homio-info:",
  "--motion-normal:",
  "--motion-slow:",
  "--ease-standard: 180ms ease;",
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
  "rgb(168 79 118 / 72%)",
  "Berry accent focus visibility"
);

/* 2. Preserve existing transition contracts */

requireContains(
  tokens,
  "--ease-standard: 180ms ease;",
  "Legacy transition compatibility"
);

requireContains(
  tokens,
  "--ease-standard-curve: cubic-bezier(",
  "Curve-only motion token"
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

/* 3. Global stylesheet imports must remain unique and ordered */

const requiredImports = [
  '@import "./styles/tokens.css";',
  '@import "./styles/base.css";',
  '@import "./styles/foundation.css";',
  '@import "./styles/motion.css";',
];

let previousPosition = -1;

for (const styleImport of requiredImports) {
  requireExactlyOnce(globals, styleImport, "Global CSS import contract");

  const currentPosition = globals.indexOf(styleImport);

  if (currentPosition <= previousPosition) {
    fail("Global CSS imports must be tokens, base, foundation, motion.");
  }

  previousPosition = currentPosition;
}

/* 4. Motion utilities and reduced-motion support */

for (const requiredClass of [
  ".motion-fade-in",
  ".motion-rise-in",
  ".motion-scale-in",
]) {
  requireContains(motion, requiredClass, "Motion utility contract");
}

requireContains(motion, ".motion-soft-reveal", "Soft reveal utility");
requireContains(
  motion,
  "@media (prefers-reduced-motion: reduce)",
  "Motion utility accessibility"
);
requireContains(
  motion,
  "var(--ease-standard-curve)",
  "Motion timing contract"
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

/* 5. Shared navigation and system modules use semantic theme tokens */

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

/* 6. Core feature page shells use the same HOMIO palette */

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

/* 7. Reject the competing navy/blue-grey palette */

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

/* 8. Existing animated modules retain reduced-motion handling */

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

/* 9. Runtime shell and theme metadata */

requireContains(layout, 'themeColor: "#f8f7f4"', "Browser theme colour");
requireContains(layout, "<AppShell>{children}</AppShell>", "Existing app shell");
requireContains(layout, "<ProductionQualityMonitor />", "Production monitor");
requireContains(layout, "<ErrorBoundary>", "Root error boundary");

/* 10. Keep the existing verification pipeline wired */

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
console.log("HOMIO DESIGN SYSTEM CONTRACT        = PASS");
console.log(`FILES VERIFIED                      = ${requiredFiles.length}`);
console.log("PREMIUM BLUSH / BERRY PALETTE         = PASS");
console.log("CHAMPAGNE ACCENT TOKEN                = PASS");
console.log("EDITORIAL TYPOGRAPHY CONTRACT        = PASS");
console.log("LEGACY TRANSITION COMPATIBILITY      = PASS");
console.log("GLOBAL CSS IMPORT ORDER              = PASS");
console.log("MOTION UTILITY CONTRACT              = PASS");
console.log("MOTION REVEAL / TYPES                = PASS");
console.log("REDUCED-MOTION ACCESSIBILITY          = PASS");
console.log("SHARED NAVIGATION / SYSTEM THEME     = PASS");
console.log("FEATURE PALETTE CONTRACT              = PASS");
console.log("LEGACY THEME COLOUR CHECK             = PASS");
console.log("ROOT SHELL / METADATA CONTRACT        = PASS");
console.log("VERIFY PIPELINE INTEGRATION           = PASS");
console.log("==================================================");
