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
  "src/components/motion/motion.types.ts"
];

for (const relativePath of requiredFiles) {
  if (!fs.existsSync(path.join(root, relativePath))) {
    fail(`Required design-system file missing: ${relativePath}`);
  }
}

const packageJson = JSON.parse(read("package.json"));
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

/* 1. Canonical HOMIO brand and surface contract */

const requiredTokens = [
  "--homio-brand: #111111;",
  "--homio-accent: #c59b63;",
  "--homio-bg: #f8f7f4;",
  "--homio-surface: #ffffff;",
  "--font-sans:",
  "--font-serif:",
  "--homio-success:",
  "--homio-warning:",
  "--homio-danger:",
  "--homio-info:",
  "--motion-normal:",
  "--motion-slow:",
  "--ease-standard: 180ms ease;",
  "--ease-standard-curve:"
];

for (const token of requiredTokens) {
  requireContains(tokens, token, "Design token contract");
}

/* 2. Preserve old transition shorthand and new curve-only contract */

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
  ["foundation.css", foundation]
]) {
  requireContains(
    source,
    "var(--ease-standard)",
    `${fileName} legacy transition compatibility`
  );
}

/* 3. Global CSS load order and unique imports */

const requiredImports = [
  '@import "./styles/tokens.css";',
  '@import "./styles/base.css";',
  '@import "./styles/foundation.css";',
  '@import "./styles/motion.css";'
];

let previousPosition = -1;

for (const styleImport of requiredImports) {
  requireExactlyOnce(globals, styleImport, "Global CSS import contract");

  const currentPosition = globals.indexOf(styleImport);

  if (currentPosition <= previousPosition) {
    fail("Global CSS import order must be tokens, base, foundation, motion.");
  }

  previousPosition = currentPosition;
}

/* 4. Motion CSS and reduced-motion support */

for (const requiredClass of [
  ".motion-fade-in",
  ".motion-rise-in",
  ".motion-scale-in"
]) {
  requireContains(motion, requiredClass, "Motion utility contract");
}

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

requireContains(
  revealCss,
  ".revealVisible",
  "Reveal component visible state"
);

requireContains(
  revealCss,
  "@media (prefers-reduced-motion: reduce)",
  "Reveal reduced-motion support"
);

requireContains(
  revealComponent,
  "IntersectionObserver",
  "Reveal viewport observer"
);

requireContains(
  revealComponent,
  "prefers-reduced-motion: reduce",
  "Reveal reduced-motion runtime contract"
);

requireContains(
  revealComponent,
  'from "./motion.types"',
  "Reveal type import"
);

requireContains(
  motionTypes,
  "export interface MotionRevealProps",
  "Reveal type definition"
);

requireContains(
  motionTypes,
  "children: ReactNode;",
  "Reveal children type"
);

/* 5. Navigation and system components must use the shared theme */

const themedModules = [
  ["GlobalMenus.module.css", globalMenus],
  ["MegaMenu.module.css", megaMenu],
  ["SharedSystem.module.css", sharedSystem],
  ["SystemComponents.module.css", systemComponents]
];

for (const [fileName, source] of themedModules) {
  requireContains(
    source,
    "var(--homio-",
    `${fileName} shared brand tokens`
  );
}

/* Reject the previous competing navy/blue-grey theme in these modules. */

const legacyPaletteValues = [
  "#15283c",
  "#14283d",
  "#14263b",
  "#152a40",
  "#1a3046",
  "#e1e8ef",
  "#e2e8ef",
  "#708095",
  "#d9bb82",
  "#d8ba82"
];

const combinedThemeModules = themedModules
  .map(([, source]) => source.toLowerCase())
  .join("\n");

for (const legacyColor of legacyPaletteValues) {
  if (combinedThemeModules.includes(legacyColor)) {
    fail(`Legacy competing theme colour remains: ${legacyColor}`);
  }
}

/* 6. Reduced-motion rules for animated system skeletons/loaders */

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

/* 7. Wire verifier into the standard frontend checks */

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
console.log("HOMIO DESIGN SYSTEM CONTRACT       = PASS");
console.log(`FILES VERIFIED                     = ${requiredFiles.length}`);
console.log("BRAND / TYPOGRAPHY TOKENS           = PASS");
console.log("LEGACY TRANSITION COMPATIBILITY     = PASS");
console.log("GLOBAL CSS IMPORT ORDER             = PASS");
console.log("MOTION UTILITY CONTRACT             = PASS");
console.log("MOTION REVEAL / TYPES               = PASS");
console.log("REDUCED-MOTION ACCESSIBILITY         = PASS");
console.log("SHARED NAVIGATION / SYSTEM THEME    = PASS");
console.log("LEGACY THEME COLOUR CHECK            = PASS");
console.log("VERIFY PIPELINE INTEGRATION          = PASS");
console.log("==================================================");
