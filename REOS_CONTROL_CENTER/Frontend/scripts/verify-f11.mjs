
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();

function read(relativePath) {
  const absolutePath = path.join(root, relativePath);

  assert.ok(
    fs.existsSync(absolutePath),
    `F11 required file is missing: ${relativePath}`,
  );

  return fs.readFileSync(absolutePath, "utf8");
}

const featureRoot = "src/features/f11_professional";

const featureFiles = [
  "README.md",
  "ProShell.tsx",
  "ProDashboard.tsx",
  "ProInventory.tsx",
  "ProInventoryDetail.tsx",
  "ProLeads.tsx",
  "ProEnquiries.tsx",
  "ProVisits.tsx",
  "ProFollowUps.tsx",
  "ProClients.tsx",
  "ProProjects.tsx",
  "ProDeals.tsx",
  "ProDocuments.tsx",
  "ProPerformance.tsx",
  "ProWorkspace.tsx",
  "ProUnavailable.tsx",
  "ProWorkspace.module.css",
  "pro.types.ts",
  "pro-server.ts",
];

const routeFiles = [
  "src/app/pro/page.tsx",
  "src/app/pro/inventory/page.tsx",
  "src/app/pro/inventory/[inventoryId]/page.tsx",
  "src/app/pro/leads/page.tsx",
  "src/app/pro/enquiries/page.tsx",
  "src/app/pro/visits/page.tsx",
  "src/app/pro/follow-ups/page.tsx",
  "src/app/pro/clients/page.tsx",
  "src/app/pro/projects/page.tsx",
  "src/app/pro/deals/page.tsx",
  "src/app/pro/documents/page.tsx",
  "src/app/pro/performance/page.tsx",
];

const featureSources = featureFiles
  .filter((file) => /\.(ts|tsx)$/.test(file))
  .map((file) => ({
    path: `${featureRoot}/${file}`,
    source: read(`${featureRoot}/${file}`),
  }));

for (const route of routeFiles) {
  const source = read(route);

  assert.match(
    source,
    /requireSignedInProPreview/,
    `${route} must enforce a signed-in session`,
  );

  assert.match(
    source,
    /ProShell/,
    `${route} must use the shared professional shell`,
  );

  assert.match(
    source,
    /robots:\s*\{\s*index:\s*false,\s*follow:\s*false\s*\}/,
    `${route} must be non-indexable`,
  );

  assert.match(
    source,
    /force-dynamic/,
    `${route} must render dynamically`,
  );
}

const allRuntimeSources = [
  ...featureSources.map((entry) => entry.source),
  ...routeFiles.map((route) => read(route)),
].join("\n");

assert.doesNotMatch(
  allRuntimeSources,
  /\bAUTONOMY_ENGINE\b|\bACRL\b|REOS_CONTROL_CENTER[\\/]+data[\\/]+state\.json/i,
  "F11 runtime must not depend on ACRL or live Control Center state",
);

const styles = read(`${featureRoot}/ProWorkspace.module.css`);

const declaredClasses = new Set(
  [...styles.matchAll(/\.([A-Za-z_][A-Za-z0-9_-]*)/g)].map(
    (match) => match[1],
  ),
);

for (const entry of featureSources.filter((item) =>
  item.path.endsWith(".tsx")
)) {
  for (const match of entry.source.matchAll(
    /styles\.([A-Za-z_][A-Za-z0-9_]*)/g
  )) {
    assert.ok(
      declaredClasses.has(match[1]),
      `${entry.path} references missing CSS class: ${match[1]}`,
    );
  }
}

const proxy = read("src/proxy.ts");

assert.doesNotMatch(
  proxy,
  /["']\/pro(?:\/[^"']*)?["']/,
  "The shared proxy must not redirect or intercept F11 routes",
);

const oidc = read("src/lib/auth/oidc.ts");

assert.ok(
  oidc.includes('"/pro/performance"'),
  "Safe return paths must include the final F11 workspace",
);

assert.match(
  oidc,
  /\\\/pro\\\/inventory\\\/\[A-Za-z0-9\]/,
  "Safe return paths must validate inventory detail identifiers",
);

const authTests = read("scripts/auth-runtime.test.mjs");

assert.ok(
  authTests.includes('"/pro"') &&
    authTests.includes("for (const pathname of approvedProPaths)") &&
    authTests.includes("auth.safeReturnTo(pathname)"),
  "Auth runtime tests must cover approved F11 return paths",
);

assert.ok(
  authTests.includes('auth.safeReturnTo("/pro/inventory/inv-123")'),
  "Auth runtime tests must cover the safe inventory detail return path",
);

const proShell = read(`${featureRoot}/ProShell.tsx`);

assert.match(
  proShell,
  /Professional role not verified/,
  "The shell must clearly disclose that professional authorization is not verified",
);

const types = read(`${featureRoot}/pro.types.ts`);

assert.match(
  types,
  /roleAuthorization:\s*false/,
  "Professional capabilities must remain disabled until verified integrations exist",
);

console.log(
  `F11 verification passed: ${featureFiles.length} feature files, ` +
    `${routeFiles.length} protected preview routes, CSS references, ` +
    `safe return paths and runtime boundaries.`,
);
