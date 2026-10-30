
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

function requireContains(source, requiredText, context) {
  if (!source.includes(requiredText)) {
    fail(`${context}: required contract missing: ${requiredText}`);
  }
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
const actionLayerSource = read(
  "src/components/shell/GlobalActionLayer.tsx",
);
const globalSearchSource = read(
  "src/components/navigation/GlobalSearch.tsx",
);
const searchFieldSource = read(
  "src/components/ui/SearchField.tsx",
);
const inputSource = read("src/components/ui/Input.tsx");
const selectSource = read("src/components/ui/Select.tsx");
const modalSource = read("src/components/ui/Modal.tsx");
const drawerSource = read("src/components/ui/Drawer.tsx");
const bottomSheetSource = read("src/components/ui/BottomSheet.tsx");
const focusHookSource = read("src/components/ui/useDialogFocus.ts");
const searchConstantsSource = read(
  "src/features/f03_search/search.constants.ts",
);

const globalStyles = read("src/app/globals.css");
const baseStyles = read("src/app/styles/base.css");
const tokenStyles = read("src/app/styles/tokens.css");
const foundationStyles = read("src/app/styles/foundation.css");

// 1. Root application and document contract

if (
  !layoutSource.includes('import "./globals.css";') ||
  !layoutSource.includes("<AppShell>{children}</AppShell>")
) {
  fail("Root layout does not load global CSS and the shared shell.");
}

requireContains(layoutSource, '<html lang="en">', "Root document language");
requireContains(layoutSource, "export const metadata", "Root metadata");
requireContains(layoutSource, "export const viewport", "Root viewport");

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
  !globalStyles.includes("#main-content") ||
  !/scroll-margin-top:\s*8rem/.test(globalStyles)
) {
  fail("Skip-link target must have an offset for the sticky header.");
}

// 2. Global styles must load in their required order

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
  globalStyles.indexOf(requiredStyleImports[0]) !==
  globalStyles.lastIndexOf(requiredStyleImports[0])
) {
  fail("Token stylesheet must be imported exactly once.");
}

if (
  globalStyles.indexOf(requiredStyleImports[1]) !==
  globalStyles.lastIndexOf(requiredStyleImports[1])
) {
  fail("Base stylesheet must be imported exactly once.");
}

if (
  globalStyles.indexOf(requiredStyleImports[2]) !==
  globalStyles.lastIndexOf(requiredStyleImports[2])
) {
  fail("Foundation stylesheet must be imported exactly once.");
}

// 3. Shared header, search and navigation must remain connected

if (
  !headerSource.includes("<GlobalSearch />") ||
  !headerSource.includes("<ResponsiveNavigation />")
) {
  fail("Shared header must mount global search and responsive navigation.");
}

requireContains(
  navigationSource,
  'className="responsive-nav"',
  "Responsive navigation",
);

if (!/<details(?:\s|>)/.test(navigationSource)) {
  fail("Keyboard-operable mobile menu disclosure is missing.");
}

requireContains(
  navigationSource,
  "<summary>Menu</summary>",
  "Keyboard-operable mobile menu trigger",
);

requireContains(
  navigationSource,
  'aria-label="Primary navigation"',
  "Desktop navigation landmark",
);

requireContains(
  navigationSource,
  'aria-label="Mobile primary navigation"',
  "Mobile navigation landmark",
);

const requiredMobileNavigationKeyboardContract = [
  "function closeMobileMenuOnEscape(",
  "KeyboardEvent<HTMLDetailsElement>",
  'if (event.key !== "Escape" || !event.currentTarget.open)',
  "event.preventDefault();",
  "event.currentTarget.open = false;",
  'event.currentTarget.querySelector("summary")?.focus();',
  "<details onKeyDown={closeMobileMenuOnEscape}>",
];

for (const contract of requiredMobileNavigationKeyboardContract) {
  requireContains(
    navigationSource,
    contract,
    "Mobile navigation keyboard dismissal",
  );
}

if (
  /className="responsive-nav__mobile-menu"[\s\S]{0,180}onKeyDown/.test(
    navigationSource,
  )
) {
  fail(
    "Escape dismissal must be handled by the disclosure so it works from both the trigger and menu links.",
  );
}

const requiredNavigationDestinations = [
  'href: "/search?intent=buy"',
  'href: "/search?intent=rent"',
  'href: "/search?intent=commercial"',
  'href: "/search?intent=projects"',
];

for (const destination of requiredNavigationDestinations) {
  requireContains(
    navigationSource,
    destination,
    "Primary navigation route contract",
  );
}

const requiredActionLinks = [
  'href="/"',
  'href="/search"',
  'href="/search?intent=projects"',
];

for (const destination of requiredActionLinks) {
  requireContains(
    actionLayerSource,
    destination,
    "Global quick-action route contract",
  );
}

requireContains(
  actionLayerSource,
  'aria-label="Global quick actions"',
  "Global quick-action landmark",
);

// 4. Global search must keep the F03 query contract and accessible feedback

const requiredSearchContract = [
  "useRouter",
  "useId",
  'new URLSearchParams({ q: normalized })',
  "router.push(`/search?${params.toString()}`)",
  "aria-invalid={status ? true : undefined}",
  "aria-describedby={status ? statusId : undefined}",
  'role="status"',
  'aria-live="polite"',
  "query.trim()",
  "if (!normalized)",
];

for (const contract of requiredSearchContract) {
  requireContains(
    globalSearchSource,
    contract,
    "Global search contract",
  );
}

if (
  globalSearchSource.includes("Search binding will activate in F03") ||
  !searchConstantsSource.includes('query: "q"')
) {
  fail("Global search and F03 query parameter contract do not match.");
}

requireContains(
  searchFieldSource,
  'type="search"',
  "Shared search field",
);

requireContains(
  searchFieldSource,
  'className={`search-field ${className}`.trim()}',
  "Shared search field styling hook",
);

// 5. Shared Input must have unique IDs and accessible error/hint association

requireContains(inputSource, "useId", "Shared Input identity");

requireContains(
  inputSource,
  "const inputId = id ?? generatedId;",
  "Shared Input identity",
);

requireContains(
  inputSource,
  '"aria-describedby": ariaDescribedBy',
  "Shared Input description merge",
);

requireContains(
  inputSource,
  "aria-describedby={describedBy}",
  "Shared Input description association",
);

requireContains(
  inputSource,
  'id={`${inputId}-hint`}',
  "Shared Input hint association",
);

requireContains(
  inputSource,
  'id={`${inputId}-error`}',
  "Shared Input error association",
);

requireContains(
  inputSource,
  'role="alert"',
  "Shared Input error announcement",
);

// 6. Shared Select must have unique IDs and accessible error/hint association

requireContains(selectSource, "useId", "Shared Select identity");

requireContains(
  selectSource,
  "const selectId = id ?? generatedId;",
  "Shared Select identity",
);

requireContains(
  selectSource,
  '"aria-describedby": ariaDescribedBy',
  "Shared Select description merge",
);

requireContains(
  selectSource,
  "aria-describedby={describedBy}",
  "Shared Select description association",
);

requireContains(
  selectSource,
  "const hintId = `${selectId}-hint`;",
  "Shared Select hint identity",
);

requireContains(
  selectSource,
  "const errorId = `${selectId}-error`;",
  "Shared Select error identity",
);

requireContains(
  selectSource,
  "id={hintId}",
  "Shared Select hint association",
);

requireContains(
  selectSource,
  "id={errorId}",
  "Shared Select error association",
);

requireContains(
  selectSource,
  'role="alert"',
  "Shared Select error announcement",
);

// 7. Modal, drawer and bottom sheet must use the same focus contract

const dialogComponents = [
  ["Modal", modalSource],
  ["Drawer", drawerSource],
  ["BottomSheet", bottomSheetSource],
];

for (const [componentName, componentSource] of dialogComponents) {
  const requiredDialogContract = [
    "useDialogFocus",
    'role="dialog"',
    'aria-modal="true"',
    "aria-labelledby={titleId}",
    "tabIndex={-1}",
    "onOpenChange(false)",
  ];

  for (const contract of requiredDialogContract) {
    requireContains(
      componentSource,
      contract,
      `${componentName} dialog contract`,
    );
  }
}

const requiredFocusHookContract = [
  'event.key === "Escape"',
  'event.key !== "Tab"',
  'document.body.style.overflow = "hidden"',
  "previousActiveElement.focus",
  "!element.closest('[aria-hidden=\"true\"], [inert]')",
  "element.getClientRects().length > 0",
  "focusableElements.length === 0",
];

for (const contract of requiredFocusHookContract) {
  requireContains(
    focusHookSource,
    contract,
    "Shared dialog focus management",
  );
}

// 8. Required shared foundation selectors must exist

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
  requireContains(
    foundationStyles,
    selector,
    "Shared foundation stylesheet",
  );
}

requireContains(
  baseStyles,
  ":focus-visible",
  "Visible keyboard focus",
);

requireContains(
  foundationStyles,
  "env(safe-area-inset-bottom)",
  "Mobile safe-area spacing",
);

requireContains(
  foundationStyles,
  "#main-content { padding-bottom: 5.25rem; }",
  "Content clearance for fixed global actions",
);

if (
  !/@media\s*\(max-width:\s*900px\)[\s\S]*?\.responsive-nav__desktop\s*\{\s*display:\s*none;/.test(
    foundationStyles,
  ) ||
  !/@media\s*\(max-width:\s*900px\)[\s\S]*?\.responsive-nav__mobile\s*\{\s*display:\s*block;/.test(
    foundationStyles,
  )
) {
  fail("Responsive navigation desktop/mobile breakpoint contract is missing.");
}

// The 320px minimum width is owned by base.css, not globals.css.

if (!/min-width:\s*320px/.test(baseStyles)) {
  fail("Base styles must retain the 320px minimum layout width.");
}

// 9. Every used shared CSS token must be declared

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

// 10. Runtime and architecture boundaries

const requiredScripts = [
  "dev",
  "build",
  "start",
  "lint",
  "typecheck",
  "verify:foundation",
  "verify:f02",
  "verify:f03",
  "verify:f04",
  "verify:f05",
  "verify",
];

for (const scriptName of requiredScripts) {
  if (!packageJson.scripts?.[scriptName]) {
    fail(`Required npm script missing: ${scriptName}`);
  }
}

const requiredVerifyCommands = [
  "npm run verify:foundation",
  "npm run verify:f02",
  "npm run verify:f03",
  "npm run verify:f04",
  "npm run verify:f05",
  "npm run typecheck",
  "npm run lint",
  "npm run build",
];

for (const command of requiredVerifyCommands) {
  requireContains(
    packageJson.scripts.verify,
    command,
    "Combined frontend verification pipeline",
  );
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

  if (
    /(?:\bfrom\s*|\bimport\s*(?:\(\s*)?)["'][^"']*ACRL/i.test(content)
  ) {
    fail(`Possible ACRL runtime import: ${relativePath}`);
  }

  if (
    /(?:\bfrom\s*|\bimport\s*(?:\(\s*)?)["'][^"']*AUTONOMY_ENGINE/i.test(
      content,
    )
  ) {
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
console.log("==================================================");
console.log("F01 FOUNDATION CONTRACT         = PASS");
console.log(`FILES VERIFIED                  = ${requiredFiles.length}`);
console.log("ROOT DOCUMENT AND SHELL         = PASS");
console.log("SKIP LINK AND STICKY OFFSET     = PASS");
console.log("RESPONSIVE NAVIGATION           = PASS");
console.log("MOBILE NAV ESCAPE DISMISSAL     = PASS");
console.log("GLOBAL SEARCH AND F03 CONTRACT  = PASS");
console.log("UNIQUE INPUT IDS / ARIA         = PASS");
console.log("UNIQUE SELECT IDS / ARIA        = PASS");
console.log("DIALOG ACCESSIBILITY CONTRACT   = PASS");
console.log("KEYBOARD FOCUS MANAGEMENT       = PASS");
console.log("CSS IMPORT ORDER                = PASS");
console.log("CSS TOKEN RESOLUTION            = PASS");
console.log("MOBILE SAFE-AREA / MOTION       = PASS");
console.log("COMBINED CI PIPELINE            = PASS");
console.log("NO STATE.JSON RUNTIME           = PASS");
console.log("NO MASTER ARCH RUNTIME          = PASS");
console.log("NO ACRL / AUTONOMY RUNTIME      = PASS");
console.log("NO PROTOTYPE IMPORT             = PASS");
console.log("==================================================");
