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
  "src/app/search/page.tsx",
  "src/app/loading.tsx",
  "src/app/error.tsx",
  "src/app/not-found.tsx",
  "src/app/globals.css",
  "src/app/styles/tokens.css",
  "src/app/styles/base.css",
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
  "src/components/ui/useDialogFocus.ts",
  "src/features/f01_experience_foundation/README.md",
  "src/features/f03_search/search.constants.ts",
];

function fail(message) {
  console.error(`FAIL-CLOSED: ${message}`);
  process.exit(1);
}

function read(relativePath) {
  const absolutePath = path.join(root, relativePath);

  if (!fs.existsSync(absolutePath)) {
    fail(`Required F01 file missing: ${relativePath}`);
  }

  return fs.readFileSync(absolutePath, "utf8");
}

for (const relativePath of requiredFiles) {
  if (!fs.existsSync(path.join(root, relativePath))) {
    fail(`Required F01 file missing: ${relativePath}`);
  }
}

const packageJson = JSON.parse(read("package.json"));
const layoutSource = read("src/app/layout.tsx");
const appShellSource = read("src/components/shell/AppShell.tsx");
const headerSource = read("src/components/shell/Header.tsx");
const navigationSource = read(
  "src/components/shell/ResponsiveNavigation.tsx",
);
const globalSearchSource = read(
  "src/components/navigation/GlobalSearch.tsx",
);
const searchConstantsSource = read(
  "src/features/f03_search/search.constants.ts",
);

const globalStyles = read("src/app/globals.css");
const baseStyles = read("src/app/styles/base.css");
const tokenStyles = read("src/app/styles/tokens.css");
const foundationStyles = read("src/app/styles/foundation.css");

const requiredStyleImports = [
  '@import "./styles/tokens.css";',
  '@import "./styles/base.css";',
  '@import "./styles/foundation.css";',
];

let previousImportPosition = -1;

for (const styleImport of requiredStyleImports) {
  const position = globalStyles.indexOf(styleImport);

  if (position < 0) {
    fail(`Required global stylesheet import missing: ${styleImport}`);
  }

  if (position <= previousImportPosition) {
    fail("Global CSS import order must be tokens, base, then foundation.");
  }

  previousImportPosition = position;
}

if (
  !layoutSource.includes('import "./globals.css";') ||
  !layoutSource.includes("<AppShell>{children}</AppShell>")
) {
  fail("Root layout does not load the shared shell and global CSS.");
}

if (!appShellSource.includes('href="#main-content"')) {
  fail("Accessible skip-to-content link is missing.");
}

if (
  !appShellSource.includes('id="main-content"') ||
  !/\btabIndex=\{-1\}/.test(appShellSource)
) {
  fail("Skip-link target must exist and be programmatically focusable.");
}

if (
  !headerSource.includes("<GlobalSearch />") ||
  !headerSource.includes("<ResponsiveNavigation />")
) {
  fail("Shared header must mount global search and responsive navigation.");
}

if (!navigationSource.includes('className="responsive-nav"')) {
  fail("Responsive navigation styling hook is missing.");
}

const requiredSearchContract = [
  "useRouter",
  "useId",
  'new URLSearchParams({ q: normalized })',
  "router.push(`/search?${params.toString()}`)",
  "aria-invalid={status ? true : undefined}",
  "aria-describedby={status ? statusId : undefined}",
];

for (const contract of requiredSearchContract) {
  if (!globalSearchSource.includes(contract)) {
    fail(`Global search contract is missing: ${contract}`);
  }
}

if (
  globalSearchSource.includes("Search binding will activate in F03") ||
  !searchConstantsSource.includes('query: "q"')
) {
  fail("Global search and F03 query parameter contract do not match.");
}

const requiredFoundationSelectors = [
  ".skip-link",
  ".site-header",
  ".responsive-nav",
  ".responsive-nav__desktop",
  ".responsive-nav__mobile-menu",
  ".site-header__search",
  ".global-search__form",
  ".context-bar",
  ".global-actions",
  "#main-content",
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

const definedTokens = new Set(
  [...tokenStyles.matchAll(/--([a-z0-9-]+)\s*:/gi)].map(
    (match) => match[1],
  ),
);

const sharedCss = `${baseStyles}\n${foundationStyles}`;

const usedTokens = new Set(
  [...sharedCss.matchAll(/var\(\s*--([a-z0-9-]+)/gi)].map(
    (match) => match[1],
  ),
);

const missingTokens = [...usedTokens].filter(
  (token) => !definedTokens.has(token),
);

if (missingTokens.length > 0) {
  fail(
    `Undefined shared CSS tokens: ${missingTokens.sort().join(", ")}`,
  );
}

const requiredScripts = [
  "dev",
  "build",
  "start",
  "lint",
  "typecheck",
  "verify:foundation",
  "verify",
];

for (const scriptName of requiredScripts) {
  if (!packageJson.scripts?.[scriptName]) {
    fail(`Required npm script missing: ${scriptName}`);
  }
}

if (!String(packageJson.engines?.node ?? "").startsWith(">=24")) {
  fail("Frontend Node.js engine requirement must remain at Node 24 or newer.");
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
  if (!fs.existsSync(directory)) {
    fail(`Required source directory missing: ${path.relative(root, directory)}`);
  }

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
console.log("ROOT SHELL MOUNTING      = PASS");
console.log("SKIP LINK FOCUS TARGET   = PASS");
console.log("GLOBAL SEARCH ROUTING    = PASS");
console.log("GLOBAL CSS IMPORT ORDER  = PASS");
console.log("CSS TOKEN RESOLUTION     = PASS");
console.log("SHARED FOUNDATION CSS    = PASS");
console.log("NODE / REACT FOUNDATION  = PASS");
console.log("NO STATE.JSON RUNTIME    = PASS");
console.log("NO MASTER ARCH RUNTIME   = PASS");
console.log("NO ACRL RUNTIME          = PASS");
console.log("NO PROTOTYPE IMPORT      = PASS");
console.log("===============================================");
