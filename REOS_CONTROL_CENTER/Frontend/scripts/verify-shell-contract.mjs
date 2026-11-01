import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();

const BRAND_WORDMARK = {
  publicPath: "/brand/homio-advisor-letter.svg",
  expectedAspectRatio: 3311.12 / 701.25,
  ratioTolerance: 0.02,
};

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

function requireExactlyOnce(source, value, context) {
  const first = source.indexOf(value);

  if (first < 0 || first !== source.lastIndexOf(value)) {
    fail(`${context}: expected exactly one occurrence of ${value}.`);
  }
}

function pass(message) {
  console.log(`PASS | ${message}`);
}

function parseSvgViewBox(source, context) {
  const rootMatch = source.match(/<svg\b[^>]*>/i);

  if (!rootMatch) {
    fail(`${context}: SVG root element is missing.`);
  }

  const viewBoxMatch = rootMatch[0].match(
    /\bviewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"/i,
  );

  if (!viewBoxMatch) {
    fail(`${context}: numeric viewBox is required.`);
  }

  const values = viewBoxMatch.slice(1).map(Number);
  const [, , width, height] = values;

  if (
    values.some((value) => !Number.isFinite(value)) ||
    width <= 0 ||
    height <= 0
  ) {
    fail(`${context}: viewBox dimensions must be finite and positive.`);
  }

  return {
    x: values[0],
    y: values[1],
    width,
    height,
    aspectRatio: width / height,
  };
}

function isRatioCompatible(actual, expected) {
  return (
    Number.isFinite(actual) &&
    Number.isFinite(expected) &&
    expected > 0 &&
    Math.abs(actual - expected) <= expected * BRAND_WORDMARK.ratioTolerance
  );
}

// 1. Original HOMIO browser emblem must be a safe,
//    self-contained 64x64 SVG.

const icon = read("src/app/icon.svg").trim();
const rootLayout = read("src/app/layout.tsx");

if (
  !/^<svg\b[\s\S]*<\/svg>$/.test(icon) ||
  !/<svg\b[^>]*xmlns="http:\/\/www\.w3\.org\/2000\/svg"[^>]*viewBox="0 0 64 64"/s.test(
    icon,
  )
) {
  fail("HOMIO browser emblem must be a valid 64x64 SVG document.");
}

// The original user-supplied emblem is a two-tone mark.
// Do not force unrelated palette colors into the logo.

for (const colour of ["#6F334B", "#352A2D"]) {
  if (!icon.includes(colour)) {
    fail(`Original HOMIO emblem is missing brand color ${colour}.`);
  }
}

if (
  /<(?:script|foreignObject|image)\b|\b(?:href|xlink:href)\s*=|url\s*\(/i.test(
    icon,
  )
) {
  fail("Browser icon must not load external resources or executable content.");
}

requireContains(rootLayout, "export const metadata", "Root metadata");
requireContains(rootLayout, '<html lang="en">', "Document language");
requireContains(
  rootLayout,
  "<AppShell>{children}</AppShell>",
  "Root application shell",
);

pass("Original HOMIO SVG browser identity and root metadata");

// 2. Original HOMIO Advisor wordmark asset must remain intact,
//    self-contained and aspect-ratio compatible.

const wordmark = read("public/brand/homio-advisor-letter.svg").trim();

if (!/^<\?xml[\s\S]*<svg\b[\s\S]*<\/svg>$|^<svg\b[\s\S]*<\/svg>$/.test(wordmark)) {
  fail("HOMIO Advisor wordmark must be a complete SVG document.");
}

const wordmarkViewBox = parseSvgViewBox(
  wordmark,
  "HOMIO Advisor wordmark",
);

if (
  !wordmark.includes("#6F334B") ||
  !wordmark.includes("#352A2D")
) {
  fail("HOMIO Advisor wordmark is missing its original two-tone brand colors.");
}

if (
  /<(?:script|foreignObject|image)\b|\b(?:href|xlink:href)\s*=|url\s*\(/i.test(
    wordmark,
  )
) {
  fail(
    "HOMIO Advisor wordmark must not contain executable content or external resources.",
  );
}

if (
  !isRatioCompatible(
    wordmarkViewBox.aspectRatio,
    BRAND_WORDMARK.expectedAspectRatio,
  )
) {
  fail(
    `HOMIO Advisor wordmark viewBox ratio ${wordmarkViewBox.aspectRatio} ` +
      "does not match the approved original artwork ratio.",
  );
}

pass(
  `Original HOMIO Advisor wordmark SVG and viewBox ratio (${wordmarkViewBox.aspectRatio.toFixed(4)})`,
);

// 3. Primary navigation must resolve to real App Router pages.

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

// 4. Every homepage secondary-navigation anchor must resolve to
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

// 5. Shared shell must retain the canonical discovery structure
//    and must render the actual original Advisor wordmark.

const appShell = read("src/components/shell/AppShell.tsx");
const header = read("src/components/shell/Header.tsx");

requireContains(appShell, 'href="#main-content"', "Accessible skip link");
requireContains(appShell, 'id="main-content"', "Skip-link destination");
requireContains(appShell, "<Header />", "Shared header mounting");
requireContains(appShell, "<ContextBar", "Shared context bar mounting");

requireContains(header, 'className="brand"', "HOMIO brand link");
requireContains(header, 'href="/"', "HOMIO home destination");
requireContains(header, 'aria-label="HOMIO home"', "HOMIO brand accessible name");

requireContains(
  header,
  'src="/brand/homio-advisor-letter.svg"',
  "Canonical HOMIO Advisor wordmark source",
);

requireContains(
  header,
  'className="brand__logo"',
  "Canonical HOMIO wordmark image class",
);

requireContains(
  header,
  'alt=""',
  "Decorative wordmark alternative text",
);

requireContains(
  header,
  "width={222}",
  "Original Advisor wordmark width contract",
);

requireContains(
  header,
  "height={47}",
  "Original Advisor wordmark height contract",
);

requireContains(
  header,
  'sizes="(max-width: 560px) 9rem, (max-width: 1100px) 12rem, 13.875rem"',
  "Responsive Advisor wordmark image sizes",
);

requireContains(
  header,
  "priority",
  "Primary header wordmark loading priority",
);

const imageElementCount = [...header.matchAll(/<Image\b/g)].length;

if (imageElementCount !== 1) {
  fail(
    `Shared HOMIO header must render exactly one brand Image; found ${imageElementCount}.`,
  );
}

const configuredDimensions = header.match(
  /width=\{(\d+)\}[\s\S]*?height=\{(\d+)\}/,
);

if (!configuredDimensions) {
  fail("HOMIO Advisor wordmark must declare numeric intrinsic dimensions.");
}

const configuredWidth = Number(configuredDimensions[1]);
const configuredHeight = Number(configuredDimensions[2]);
const configuredRatio = configuredWidth / configuredHeight;

if (
  !isRatioCompatible(
    configuredRatio,
    wordmarkViewBox.aspectRatio,
  )
) {
  fail(
    `Header image ratio ${configuredRatio.toFixed(4)} does not preserve ` +
      `the original SVG ratio ${wordmarkViewBox.aspectRatio.toFixed(4)}.`,
  );
}

requireContains(header, "<GlobalSearch />", "Shared global search");
requireContains(
  header,
  "<ResponsiveNavigation />",
  "Shared responsive navigation",
);

pass("Original Advisor wordmark is mounted through the canonical header asset");
pass(
  `Header image dimensions preserve the original wordmark ratio (${configuredWidth}x${configuredHeight})`,
);
pass("Shared application shell structure and navigation mounting");

console.log("");
console.log("==================================================");
console.log("HOMIO SHELL CONTRACT VERIFICATION = PASS");
console.log(`PRIMARY ROUTES VERIFIED           = ${checkedRoutes.size}`);
console.log(`HOMEPAGE ANCHORS VERIFIED         = ${expectedAnchors.length}`);
console.log("ORIGINAL BROWSER ICON CONTRACT     = PASS");
console.log("ORIGINAL ADVISOR WORDMARK CONTRACT = PASS");
console.log("ROOT DOCUMENT CONTRACT            = PASS");
console.log("SHARED SHELL MOUNTING              = PASS");
console.log("==================================================");
