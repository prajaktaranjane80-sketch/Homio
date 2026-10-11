import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();

const requiredFiles = [
  "package.json",
  "next.config.ts",
  "tsconfig.json",
  "eslint.config.mjs",
  "next-env.d.ts",
  "src/app/layout.tsx",
  "src/app/page.tsx",
  "src/app/loading.tsx",
  "src/app/error.tsx",
  "src/app/not-found.tsx",
  "src/app/globals.css",
  "src/app/styles/foundation.css",
  "src/components/shell/AppShell.tsx",
  "src/components/shell/Header.tsx",
  "src/components/shell/ResponsiveNavigation.tsx",
  "src/components/shell/ContextBar.tsx",
  "src/components/shell/PageContainer.tsx",
  "src/components/shell/GlobalActionLayer.tsx",
  "src/components/navigation/GlobalSearch.tsx",
  "src/components/navigation/Breadcrumbs.tsx",
  "src/components/ui/Button.tsx",
  "src/components/ui/Input.tsx",
  "src/components/ui/SearchField.tsx",
  "src/components/ui/Select.tsx",
  "src/components/ui/Chip.tsx",
  "src/components/ui/Badge.tsx",
  "src/components/ui/Card.tsx",
  "src/components/ui/Tabs.tsx",
  "src/components/ui/Toast.tsx",
  "src/components/ui/Modal.tsx",
  "src/components/ui/Drawer.tsx",
  "src/components/ui/BottomSheet.tsx",
  "src/components/ui/Skeleton.tsx",
  "src/components/ui/EmptyState.tsx",
  "src/components/ui/ErrorState.tsx",
  "src/features/f01_experience_foundation/README.md",
];

function fail(message) {
  console.error(`FAIL-CLOSED: ${message}`);
  process.exit(1);
}

for (const relativePath of requiredFiles) {
  const absolutePath = path.join(root, relativePath);

  if (!fs.existsSync(absolutePath)) {
    fail(`Required F01 file missing: ${relativePath}`);
  }
}

const packageJson = JSON.parse(
  fs.readFileSync(path.join(root, "package.json"), "utf8"),
);

const globalStylesPath = path.join(root, "src/app/globals.css");
const foundationStylesPath = path.join(
  root,
  "src/app/styles/foundation.css",
);

const globalStyles = fs.readFileSync(globalStylesPath, "utf8");
const foundationStyles = fs.readFileSync(
  foundationStylesPath,
  "utf8",
);

if (!globalStyles.includes('@import "./styles/foundation.css";')) {
  fail("Shared foundation stylesheet is not imported by globals.css.");
}

const requiredFoundationSelectors = [
  ".skip-link",
  ".site-header",
  ".responsive-nav__desktop",
  ".responsive-nav__mobile-menu",
  ".site-header__search",
  ".global-search__form",
  ".context-bar",
  ".global-actions",
  ".page-container",
  ".field-group",
  ".input-field",
  ".search-field",
  ".select-field",
  ".button--small",
  ".button--ghost",
  ".badge",
  ".chip",
  ".tabs",
  ".overlay",
  ".drawer-overlay__panel",
  ".sheet-overlay__panel",
  ".toast",
  ".skeleton",
  ".empty-state",
  ".error-state",
  "@media (prefers-reduced-motion: reduce)",
];

for (const selector of requiredFoundationSelectors) {
  if (!foundationStyles.includes(selector)) {
    fail(`Shared foundation style is missing: ${selector}`);
  }
}

const requiredScripts = [
  "dev",
  "build",
  "start",
  "lint",
  "typecheck",
  "verify:foundation",
];

for (const scriptName of requiredScripts) {
  if (!packageJson.scripts?.[scriptName]) {
    fail(`Required npm script missing: ${scriptName}`);
  }
}

if (!packageJson.dependencies?.next) {
  fail("Next.js dependency missing.");
}

if (!packageJson.dependencies?.react) {
  fail("React dependency missing.");
}

if (!packageJson.dependencies?.["react-dom"]) {
  fail("React DOM dependency missing.");
}

if (!packageJson.devDependencies?.typescript) {
  fail("TypeScript dependency missing.");
}

function walk(directory) {
  const entries = fs.readdirSync(directory, {
    withFileTypes: true,
  });

  const files = [];

  for (const entry of entries) {
    if (
      entry.name === "node_modules" ||
      entry.name === ".next" ||
      entry.name === "build" ||
      entry.name === "out"
    ) {
      continue;
    }

    const absolute = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      files.push(...walk(absolute));
    } else {
      files.push(absolute);
    }
  }

  return files;
}

const sourceRoot = path.join(root, "src");

const sourceFiles = walk(sourceRoot).filter((file) =>
  /\.(ts|tsx|js|jsx|mjs)$/.test(file),
);

for (const file of sourceFiles) {
  const content = fs.readFileSync(file, "utf8");
  const relativePath = path.relative(root, file);

  if (content.includes("REOS_CONTROL_CENTER/data/state.json")) {
    fail(`Frontend runtime reads state.json: ${relativePath}`);
  }

  if (content.includes("HOMIO_REOS_MASTER_ARCHITECTURE.json")) {
    fail(`Frontend runtime reads Master Architecture JSON: ${relativePath}`);
  }

  if (/\bfrom\s+["'][^"']*ACRL/i.test(content)) {
    fail(`Possible ACRL runtime import: ${relativePath}`);
  }

  if (/\bimport\s+["'][^"']*AUTONOMY_ENGINE/i.test(content)) {
    fail(`Possible backend/autonomy runtime import: ${relativePath}`);
  }
}

const prototypeImports = sourceFiles.filter((file) =>
  fs.readFileSync(file, "utf8").includes("Frontend/index.html"),
);

if (prototypeImports.length > 0) {
  fail("Production source imports the static prototype.");
}

console.log("");
console.log("===============================================");
console.log("F01 FOUNDATION CONTRACT = PASS");
console.log(`FILES VERIFIED           = ${requiredFiles.length}`);
console.log("SHARED FOUNDATION CSS    = PASS");
console.log("NEXT/REACT FOUNDATION    = PASS");
console.log("NO STATE.JSON RUNTIME    = PASS");
console.log("NO MASTER ARCH RUNTIME   = PASS");
console.log("NO ACRL RUNTIME          = PASS");
console.log("NO PROTOTYPE IMPORT      = PASS");
console.log("===============================================");
