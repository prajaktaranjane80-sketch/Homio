
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
    fail(`Required shell contract file missing: ${relativePath}`);
  }

  return fs.readFileSync(absolutePath, "utf8");
}

function requireContains(source, value, context) {
  if (!source.includes(value)) {
    fail(`${context}: required contract missing: ${value}`);
  }
}

function pass(message) {
  console.log(`PASS | ${message}`);
}

// 1. Browser icon must exist and remain a safe, self-contained SVG.

const icon = read("src/app/icon.svg").trim();
const rootLayout = read("src/app/layout.tsx");

if (
  !/^<svg\b[\s\S]*<\/svg>$/.test(icon) ||
  !/<svg\b[^>]*xmlns="http:\/\/www\.w3\.org\/2000\/svg"[^>]*viewBox="0 0 64 64"/s.test(
    icon,
  )
) {
  fail("HOMIO browser icon must be a valid 64x64 SVG document.");
}

for (const colour of [
  "#6F334B",
  "#F8F1E7",
  "#F3DDE4",
]) {
  if (!icon.includes(colour)) {
    fail(`HOMIO browser icon is missing canonical brand colour ${colour}.`);
  }
}

if (
  /<(?:script|foreignObject|image)\b|\b(?:href|xlink:href)\s*=|url\s*\(/i.test(
    icon,
  )
) {
  fail("Browser icon must not load external resources or executable content.");
}

requireContains(rootLayout, 'export const metadata', "Root metadata");
requireContains(rootLayout, '<html lang="en">', "Document language");
requireContains(
  rootLayout,
  "<AppShell>{children}</AppShell>",
  "Root application shell",
);

pass("HOMIO SVG browser identity and root metadata");

// 2. Primary navigation must resolve to real App Router pages.

const primaryNavigation = read(
  "src/components/shell/ResponsiveNavigation.tsx",
);

const primaryDestinations = [
  ...primaryNavigation.matchAll(/href:\s*"([^"]+)"/g),
].map((match) => match[1]);

if (primaryDestinations.length === 0) {
  fail("Primary navigation has no registered destinations.");
}

const checkedRoutes = new Set();

for (const destination of primaryDestinations) {
  let route;

  try {
    route = new URL(destination, "https://homio.invalid").pathname;
  } catch {
    fail(`Invalid primary navigation destination: ${destination}`);
  }

  const routeFile =
    route === "/"
      ? "src/app/page.tsx"
      : `src/app${route}/page.tsx`;

  if (!fs.existsSync(path.join(root, routeFile))) {
    fail(
      `Primary navigation destination ${destination} has no App Router page: ${routeFile}`,
    );
  }

  checkedRoutes.add(route);
}

pass(
  `Primary navigation destinations resolve (${checkedRoutes.size} unique routes)`,
);

// 3. Every homepage secondary-navigation anchor must resolve to
//    one real section which is actually mounted on the homepage.

const secondaryNavigation = read(
  "src/features/f02_home_discovery/HomeSecondaryNav.tsx",
);

const homepage = read(
  "src/features/f02_home_discovery/HomeDiscoveryPage.tsx",
);

const anchorTargets = [
  ...secondaryNavigation.matchAll(
    /href\s*(?::|=)\s*["'](#[a-z0-9-]+)["']/gi,
  ),
].map((match) => match[1]);

const expectedAnchors = [
  "#explore",
  "#locations",
  "#projects",
  "#commercial",
  "#tools",
  "#advice",
  "#post-property",
];

if (
  anchorTargets.length !== expectedAnchors.length ||
  new Set(anchorTargets).size !== expectedAnchors.length
) {
  fail(
    "Homepage secondary navigation must contain exactly seven unique section links.",
  );
}

for (const expected of expectedAnchors) {
  if (!anchorTargets.includes(expected)) {
    fail(`Homepage secondary navigation is missing ${expected}.`);
  }
}

const sectionOwners = {
  explore: "HomeQuickDiscovery",
  locations: "PopularCities",
  projects: "FeaturedProjects",
  commercial: "CommercialSection",
  tools: "PropertyTools",
  advice: "HomioAdvice",
  "post-property": "PostPropertySection",
};

for (const [anchor, component] of Object.entries(sectionOwners)) {
  const componentPath =
    `src/features/f02_home_discovery/${component}.tsx`;

  const componentSource = read(componentPath);

  requireContains(
    componentSource,
    `id="${anchor}"`,
    `Homepage section target ${anchor}`,
  );

  requireContains(
    homepage,
    `import ${component} from "./${component}";`,
    `Homepage section mounting ${component}`,
  );
}

pass("All seven homepage navigation anchors resolve to mounted sections");

// 4. The shared shell must retain the canonical discovery structure.

const appShell = read("src/components/shell/AppShell.tsx");
const header = read("src/components/shell/Header.tsx");

requireContains(appShell, 'href="#main-content"', "Accessible skip link");
requireContains(appShell, 'id="main-content"', "Skip-link destination");
requireContains(appShell, "<Header />", "Shared header mounting");
requireContains(appShell, "<ContextBar", "Shared context bar mounting");

requireContains(header, "<GlobalSearch />", "Shared global search");
requireContains(
  header,
  "<ResponsiveNavigation />",
  "Shared responsive navigation",
);

pass("Shared application shell structure and navigation mounting");

console.log("");
console.log("==================================================");
console.log("HOMIO SHELL CONTRACT VERIFICATION = PASS");
console.log(`PRIMARY ROUTES VERIFIED           = ${checkedRoutes.size}`);
console.log(`HOMEPAGE ANCHORS VERIFIED         = ${expectedAnchors.length}`);
console.log("BROWSER ICON CONTRACT             = PASS");
console.log("ROOT DOCUMENT CONTRACT            = PASS");
console.log("SHARED SHELL MOUNTING              = PASS");
console.log("==================================================");
