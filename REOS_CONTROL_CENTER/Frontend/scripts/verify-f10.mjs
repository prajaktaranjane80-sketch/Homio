
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(scriptDirectory, "..");
const f10Root = "src/features/f10_transaction";

function absolute(relativePath) {
  return path.join(frontendRoot, relativePath);
}

function read(relativePath) {
  const targetPath = absolute(relativePath);

  assert.ok(
    fs.existsSync(targetPath),
    `Required file is missing: ${relativePath}`,
  );

  return fs.readFileSync(targetPath, "utf8");
}

const requiredModules = [
  "README.md",
  "TransactionShell.tsx",
  "DealOverview.tsx",
  "DealParties.tsx",
  "DealProperty.tsx",
  "OfferSummary.tsx",
  "OfferStatus.tsx",
  "NegotiationPanel.tsx",
  "DocumentChecklist.tsx",
  "TransactionMilestones.tsx",
  "TransactionFinancialStatus.tsx",
  "TransactionStatus.tsx",
  "CommissionStatus.tsx",
  "DealCompletion.tsx",
  "TransactionAccessNotice.tsx",
  "TransactionEmptyState.tsx",
  "transaction.types.ts",
  "transaction.constants.ts",
  "TransactionWorkspace.module.css",
];

const sources = new Map(
  requiredModules.map((name) => [
    name,
    read(`${f10Root}/${name}`),
  ]),
);

const css = sources.get("TransactionWorkspace.module.css");
const cssOpenBraces = (css.match(/{/g) ?? []).length;
const cssCloseBraces = (css.match(/}/g) ?? []).length;

assert.equal(
  cssOpenBraces,
  cssCloseBraces,
  "F10 CSS has unmatched braces.",
);
assert.ok(css.trimEnd().endsWith("}"), "F10 CSS appears truncated.");

const emptyStateRule = css.match(
  /\.emptyStatePage\s*\{([^}]*)\}/,
);

assert.ok(
  emptyStateRule,
  "F10 CSS is missing the empty-state page selector.",
);

for (const variable of [
  "--f10-ink",
  "--f10-ink-strong",
  "--f10-muted",
  "--f10-subtle",
  "--f10-line",
  "--f10-surface",
  "--f10-canvas",
  "--f10-accent",
  "--f10-accent-dark",
  "--f10-accent-soft",
  "--f10-teal",
  "--f10-radius",
  "--f10-shadow",
]) {
  assert.ok(
    emptyStateRule[1].includes(`${variable}:`),
    `F10 empty-state CSS is missing ${variable}.`,
  );
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const styleNames = new Set();

for (const [name, source] of sources) {
  if (!/\.(tsx|ts)$/.test(name)) continue;

  for (const match of source.matchAll(
    /styles\.([A-Za-z_][A-Za-z0-9_]*)/g,
  )) {
    styleNames.add(match[1]);
  }

  for (const match of source.matchAll(
    /from\s+["'](\.[^"']+)["']/g,
  )) {
    const basePath = path.join(
      absolute(f10Root),
      match[1],
    );

    const candidates = [
      basePath,
      `${basePath}.tsx`,
      `${basePath}.ts`,
      `${basePath}.css`,
    ];

    assert.ok(
      candidates.some((candidate) => fs.existsSync(candidate)),
      `${name} has an unresolved relative import: ${match[1]}`,
    );
  }
}

const missingStyles = [...styleNames].filter((name) => {
  const escaped = escapeRegExp(name);
  return !new RegExp(
    `\\.${escaped}(?=[\\s.:#[,>+~{])`,
  ).test(css);
});

assert.deepEqual(
  missingStyles,
  [],
  `F10 CSS classes are missing: ${missingStyles.join(", ")}`,
);

for (const toneClass of [
  "tonePositive",
  "toneWarning",
  "toneDanger",
  "toneInfo",
  "toneNeutral",
]) {
  assert.match(
    css,
    new RegExp(`\\.${toneClass}\\s*\\{`),
    `Missing status tone style: ${toneClass}`,
  );
}

const shell = sources.get("TransactionShell.tsx");

for (const requiredFeature of [
  "DealOverview",
  "DealParties",
  "DealProperty",
  "OfferSummary",
  "NegotiationPanel",
  "DocumentChecklist",
  "TransactionMilestones",
  "TransactionFinancialStatus",
  "TransactionStatusPanel",
  "CommissionStatus",
  "DealCompletion",
]) {
  assert.ok(
    shell.includes(requiredFeature),
    `TransactionShell does not reference ${requiredFeature}.`,
  );
}

assert.match(shell, /role="tablist"/);
assert.match(shell, /role="tabpanel"/);
assert.match(shell, /onKeyDown=/);

for (const key of [
  "ArrowRight",
  "ArrowLeft",
  "Home",
  "End",
]) {
  assert.ok(
    shell.includes(`"${key}"`),
    `Transaction tabs are missing ${key} keyboard handling.`,
  );
}

const route = read(
  "src/app/transaction/[transactionId]/page.tsx",
);
const oidc = read("src/lib/auth/oidc.ts");
const loginPage = read("src/app/login/page.tsx");
const authPanel = read("src/features/authentication/AuthPanel.tsx");
const authTests = read("scripts/auth-runtime.test.mjs");

assert.match(route, /readSessionCookie/);
assert.match(route, /SESSION_COOKIE/);
assert.match(route, /if\s*\(!session\)/);
assert.match(route, /redirect\(/);
assert.match(route, /TRANSACTION_ID_PATTERN\.test\(transactionId\)/);
assert.match(route, /<TransactionShell\s*\/>/);
assert.match(route, /index:\s*false/);

assert.match(loginPage, /safeReturnTo\(params\.returnTo\)/);
assert.match(authPanel, /name="returnTo"/);
assert.match(authPanel, /returnTo \?\? "\/my"/);
assert.match(oidc, /\/transaction\\?\/?\[?A-Za-z0-9/);
assert.match(
  authTests,
  /safeReturnTo\("\/transaction\/tx-123"\)/,
);

const runtimeSources = [
  ...[...sources.entries()]
    .filter(([name]) => /\.(tsx|ts)$/.test(name))
    .map(([, source]) => source),
  route,
];

for (const source of runtimeSources) {
  assert.doesNotMatch(
    source,
    /AUTONOMY_ENGINE|REOS_CONTROL_CENTER[/\\]data[/\\]state\.json/,
    "F10 must not depend on backend engineering tools at runtime.",
  );
}

const manifest = JSON.parse(read("package.json"));

assert.equal(
  manifest.scripts["verify:f10"],
  "node ./scripts/verify-f10.mjs",
  "F10 verifier must be registered in package.json.",
);

assert.ok(
  manifest.scripts.verify.includes("npm run verify:f10"),
  "F10 must be included in the complete verification sequence.",
);

console.log("F10 REQUIRED MODULES = PASS");
console.log("F10 CSS SYNTAX AND SELECTORS = PASS");
console.log("F10 EMPTY-STATE VARIABLES = PASS");
console.log("F10 RELATIVE IMPORTS = PASS");
console.log("F10 TRANSACTION SECTIONS = PASS");
console.log("F10 KEYBOARD TAB NAVIGATION = PASS");
console.log("F10 AUTH-GATED ROUTE = PASS");
console.log("F10 SAFE AUTH RETURN PATH = PASS");
console.log("F10 NO FORBIDDEN BACKEND RUNTIME COUPLING = PASS");
console.log("F10 INCLUDED IN FULL VERIFY = PASS");
