import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const sourceRoot = path.join(root, "src");
const appRoot = path.join(sourceRoot, "app");
const featureRoot = path.join(sourceRoot, "features/f02_home_discovery");
const legacyRoot = path.join(sourceRoot, "components/home");

function fail(message) {
  console.error(`FAIL-CLOSED: ${message}`);
  process.exit(1);
}

function walk(directory) {
  if (!fs.existsSync(directory)) {
    return [];
  }

  const files = [];

  for (const entry of fs.readdirSync(directory, {
    withFileTypes: true,
  })) {
    const absolute = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      files.push(...walk(absolute));
    } else {
      files.push(absolute);
    }
  }

  return files;
}

function read(relativePath) {
  const absolutePath = path.join(root, relativePath);

  if (!fs.existsSync(absolutePath)) {
    fail(`Required file missing: ${relativePath}`);
  }

  return fs.readFileSync(absolutePath, "utf8");
}

function requireContains(source, requiredText, context) {
  if (!source.includes(requiredText)) {
    fail(`${context}: required contract missing: ${requiredText}`);
  }
}

function routeRegexFromPageFile(file) {
  const relative = path.relative(appRoot, file);
  const segments = relative
    .split(path.sep)
    .slice(0, -1)
    .filter((segment) => !/^\(.+\)$/.test(segment));

  if (segments.length === 0) {
    return /^\/$/;
  }

  const regexSegments = segments.map((segment) => {
    if (/^\[\[\.\.\.[^\]]+\]\]$/.test(segment)) {
      return "(?:.+)?";
    }

    if (/^\[\.\.\.[^\]]+\]$/.test(segment)) {
      return ".+";
    }

    if (/^\[[^\]]+\]$/.test(segment)) {
      return "[^/]+";
    }

    return segment.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  });

  return new RegExp(`^/${regexSegments.join("/")}$`);
}

function getHrefLiterals(source) {
  const matches = [];
  const pattern =
    /\bhref\s*=\s*(?:"([^"]+)"|'([^']+)'|{\s*`([^`]+)`\s*})|\bhref\s*:\s*(?:"([^"]+)"|'([^']+)')/g;

  for (const match of source.matchAll(pattern)) {
    const value =
      match[1] ??
      match[2] ??
      match[3] ??
      match[4] ??
      match[5];

    if (value) {
      matches.push(value);
    }
  }

  return matches;
}

function getPropertyIds(source) {
  return new Set(
    [...source.matchAll(/["']([^"']+)["']\s*:\s*createPropertyPreview\(/g)]
      .map((match) => match[1]),
  );
}

function getProjectIds(source) {
  const ids = new Set(
    [...source.matchAll(/["']([^"']+)["']\s*:\s*createProjectPreview\(/g)]
      .map((match) => match[1]),
  );

  const primaryProject = source.match(
    /export const PROJECT_PREVIEW:[\s\S]*?\bid:\s*"([^"]+)"/,
  );

  if (primaryProject?.[1]) {
    ids.add(primaryProject[1]);
  }

  return ids;
}

const featureFiles = walk(featureRoot);

if (!featureFiles.length) {
  fail("F02 feature directory is missing or empty.");
}

const componentFiles = featureFiles.filter(
  (file) =>
    file.endsWith(".tsx") &&
    path.basename(file) !== "HomeDiscoveryPage.tsx",
);

const styleFiles = featureFiles.filter((file) =>
  file.endsWith(".module.css"),
);

if (!fs.existsSync(path.join(featureRoot, "HomeDiscoveryPage.tsx"))) {
  fail("F02 HomeDiscoveryPage.tsx is missing.");
}

if (!fs.existsSync(path.join(featureRoot, "README.md"))) {
  fail("F02 README is missing.");
}

if (componentFiles.length !== 43) {
  fail(
    `Expected 43 homepage components excluding HomeDiscoveryPage.tsx; found ${componentFiles.length}.`,
  );
}

if (styleFiles.length !== 43) {
  fail(`Expected 43 CSS modules; found ${styleFiles.length}.`);
}

for (const component of componentFiles) {
  const cssPath = component.replace(/\.tsx$/, ".module.css");

  if (!fs.existsSync(cssPath)) {
    fail(`CSS module missing for ${path.basename(component)}.`);
  }
}

for (const styleFile of styleFiles) {
  if (!fs.readFileSync(styleFile, "utf8").trim()) {
    fail(`Empty CSS module: ${path.relative(root, styleFile)}.`);
  }
}

if (
  fs.existsSync(legacyRoot) &&
  fs.readdirSync(legacyRoot).length > 0
) {
  fail("Legacy src/components/home still contains files.");
}

const routeEntry = path.join(appRoot, "page.tsx");
const routeSource = read("src/app/page.tsx");

requireContains(
  routeSource,
  '@/features/f02_home_discovery/HomeDiscoveryPage',
  "Homepage route composition",
);

if (!fs.existsSync(routeEntry)) {
  fail("Homepage route src/app/page.tsx is missing.");
}

const appPageFiles = walk(appRoot).filter((file) =>
  /(^|[/\\])page\.tsx$/.test(file),
);

const routeMatchers = appPageFiles.map((file) => ({
  file,
  regex: routeRegexFromPageFile(file),
}));

if (!routeMatchers.some(({ regex }) => regex.test("/"))) {
  fail("No root homepage route was registered.");
}

const sourceFiles = walk(sourceRoot).filter((file) =>
  /\.(ts|tsx|js|jsx)$/.test(file),
);

const allSource = sourceFiles.map((file) => ({
  file,
  content: fs.readFileSync(file, "utf8"),
}));

const allSourceContent = allSource.map((item) => item.content).join("\n");

const anchorIds = new Set();

for (const { content } of allSource) {
  for (const match of content.matchAll(/\bid\s*=\s*"([^"]+)"/g)) {
    anchorIds.add(match[1]);
  }
}

const searchConstants = read(
  "src/features/f03_search/search.constants.ts",
);

const queryKeyMatch = searchConstants.match(
  /export const SEARCH_QUERY_KEYS = \{([\s\S]*?)\} as const;/,
);

if (!queryKeyMatch) {
  fail("F03 SEARCH_QUERY_KEYS contract was not found.");
}

const supportedSearchKeys = new Set(
  [...queryKeyMatch[1].matchAll(/:\s*"([^"]+)"/g)].map(
    (match) => match[1],
  ),
);

const propertyData = read(
  "src/features/f04_property/property.data.ts",
);
const projectData = read(
  "src/features/f05_project/project.data.ts",
);

const knownPropertyIds = getPropertyIds(propertyData);
const knownProjectIds = getProjectIds(projectData);

let checkedLinks = 0;
let checkedSearchLinks = 0;
let checkedAnchors = 0;

for (const file of featureFiles.filter((item) => item.endsWith(".tsx"))) {
  const content = fs.readFileSync(file, "utf8");

  for (const rawHref of getHrefLiterals(content)) {
    if (/^(https?:|mailto:|tel:|\/\/)/i.test(rawHref)) {
      continue;
    }

    let url;

    try {
      url = new URL(rawHref, "https://homio.invalid");
    } catch {
      fail(`Invalid href "${rawHref}" in ${path.relative(root, file)}.`);
    }

    if (url.origin !== "https://homio.invalid") {
      continue;
    }

    const pathname =
      url.pathname.replace(/\/+$/, "") || "/";

    const hasRoute = routeMatchers.some(({ regex }) =>
      regex.test(pathname),
    );

    if (!hasRoute) {
      fail(
        `Broken internal route "${rawHref}" in ${path.relative(root, file)}.`,
      );
    }

    if (url.hash && pathname === "/") {
      const targetId = decodeURIComponent(url.hash.slice(1));

      if (!anchorIds.has(targetId)) {
        fail(
          `Missing homepage anchor "#${targetId}" referenced in ${path.relative(root, file)}.`,
        );
      }

      checkedAnchors += 1;
    }

    if (pathname === "/search") {
      for (const key of url.searchParams.keys()) {
        if (!supportedSearchKeys.has(key)) {
          fail(
            `Unsupported search query key "${key}" in "${rawHref}" (${path.relative(root, file)}).`,
          );
        }
      }

      checkedSearchLinks += 1;
    }

    if (pathname.startsWith("/property/")) {
      const propertyId = pathname.split("/")[2];

      if (!propertyId || !knownPropertyIds.has(propertyId)) {
        fail(
          `Property preview ID "${propertyId ?? ""}" is not registered in property.data.ts.`,
        );
      }
    }

    if (pathname.startsWith("/project/")) {
      const projectId = pathname.split("/")[2];

      if (!projectId || !knownProjectIds.has(projectId)) {
        fail(
          `Project preview ID "${projectId ?? ""}" is not registered in project.data.ts.`,
        );
      }
    }

    checkedLinks += 1;
  }
}

const importPattern =
  /\bfrom\s+["']([^"']+)["']|^\s*import\s+["']([^"']+)["']/gm;

const extensions = [".ts", ".tsx", ".js", ".jsx", ".css", ".json"];

for (const { file, content } of allSource) {
  if (content.includes("@/components/home/")) {
    fail(
      `Legacy homepage import remains in ${path.relative(root, file)}.`,
    );
  }

  if (!file.startsWith(featureRoot + path.sep)) {
    continue;
  }

  for (const match of content.matchAll(importPattern)) {
    const specifier = match[1] || match[2];

    if (!specifier.startsWith(".")) {
      continue;
    }

    const candidate = path.resolve(path.dirname(file), specifier);

    const exists =
      fs.existsSync(candidate) ||
      extensions.some((extension) =>
        fs.existsSync(candidate + extension),
      );

    if (!exists) {
      fail(
        `Unresolved relative import in ${path.relative(root, file)}: ${specifier}`,
      );
    }
  }
}

const requiredPreviewFiles = [
  "OwnerProperties.tsx",
  "FreshProperties.tsx",
  "VerifiedProperties.tsx",
  "FeaturedProjects.tsx",
  "BuilderProjects.tsx",
  "NewProjectCollections.tsx",
  "SaveCompareSection.tsx",
  "HomioAISection.tsx",
];

for (const filename of requiredPreviewFiles) {
  const content = read(
    `src/features/f02_home_discovery/${filename}`,
  );

  if (!/preview/i.test(content)) {
    fail(
      `${filename} must disclose that its static data/UI is a preview.`,
    );
  }
}

const ownerProperties = read(
  "src/features/f02_home_discovery/OwnerProperties.tsx",
);
const freshProperties = read(
  "src/features/f02_home_discovery/FreshProperties.tsx",
);
const verifiedProperties = read(
  "src/features/f02_home_discovery/VerifiedProperties.tsx",
);
const homeSearch = read(
  "src/features/f02_home_discovery/HomeSearch.tsx",
);
const homioAI = read(
  "src/features/f02_home_discovery/HomioAISection.tsx",
);

requireContains(
  ownerProperties,
  "not verified",
  "Owner-origin disclosure",
);
requireContains(
  freshProperties,
  "not verified",
  "Property preview disclosure",
);
requireContains(
  verifiedProperties,
  "not verified",
  "Verified-property preview disclosure",
);
requireContains(
  homeSearch,
  'params.set("intent", intent)',
  "F02-to-F03 intent contract",
);
requireContains(
  homeSearch,
  'params.set("q", normalizedQuery)',
  "F02-to-F03 query contract",
);
requireContains(
  homioAI,
  "AI interaction preview only",
  "AI capability disclosure",
);

if (/AI available|aria-label="AI available"|>Ready</i.test(homioAI)) {
  fail("HOMIO AI preview must not claim that an active AI service is available.");
}

const buttonTags = featureFiles
  .filter((file) => file.endsWith(".tsx"))
  .flatMap((file) => {
    const content = fs.readFileSync(file, "utf8");

    return [...content.matchAll(/<button\b[\s\S]*?>/g)].map(
      (match) => ({
        file,
        tag: match[0],
      }),
    );
  });

for (const { file, tag } of buttonTags) {
  if (
    /\btype\s*=\s*["']button["']/.test(tag) &&
    !/\bonClick\s*=/.test(tag) &&
    !/\bdisabled(?:\s|=|\/|>)/.test(tag)
  ) {
    fail(
      `Unwired enabled button in ${path.relative(root, file)}: ${tag.replace(/\s+/g, " ").slice(0, 140)}`,
    );
  }
}

console.log("");
console.log("==================================================");
console.log("F02 HOME DISCOVERY HARDENED CONTRACT = PASS");
console.log("43 COMPONENTS / 43 CSS MODULES        = PASS");
console.log("HOMEPAGE ROUTE COMPOSITION            = PASS");
console.log(`INTERNAL ROUTES CHECKED                = ${checkedLinks}`);
console.log(`SEARCH LINKS CHECKED                   = ${checkedSearchLinks}`);
console.log(`HOMEPAGE ANCHORS CHECKED               = ${checkedAnchors}`);
console.log("PROPERTY DETAIL IDS REGISTERED         = PASS");
console.log("PROJECT DETAIL IDS REGISTERED          = PASS");
console.log("SEARCH QUERY KEYS SUPPORTED            = PASS");
console.log("PREVIEW / INVENTORY DISCLOSURES         = PASS");
console.log("NO UNWIRED ENABLED TYPE=BUTTON CONTROLS = PASS");
console.log("RELATIVE IMPORTS                        = PASS");
console.log("LEGACY DIRECTORY CLEANUP                = PASS");
console.log("NO LEGACY HOMEPAGE IMPORTS              = PASS");
console.log("==================================================");
