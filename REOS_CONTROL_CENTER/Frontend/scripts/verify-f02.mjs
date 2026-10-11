import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const featureRoot = path.join(root, "src/features/f02_home_discovery");
const legacyRoot = path.join(root, "src/components/home");

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

if (!fs.existsSync(path.join(featureRoot, "HomeDiscoveryPage.tsx"))) {
  fail("F02 HomeDiscoveryPage.tsx is missing.");
}

if (!fs.existsSync(path.join(featureRoot, "README.md"))) {
  fail("F02 README is missing.");
}

const featureFiles = walk(featureRoot);

const componentFiles = featureFiles.filter(
  (file) =>
    file.endsWith(".tsx") &&
    path.basename(file) !== "HomeDiscoveryPage.tsx",
);

const styleFiles = featureFiles.filter((file) =>
  file.endsWith(".module.css"),
);

if (componentFiles.length !== 43) {
  fail(
    `Expected 43 migrated homepage components; found ${componentFiles.length}.`,
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

if (
  fs.existsSync(legacyRoot) &&
  fs.readdirSync(legacyRoot).length > 0
) {
  fail("Legacy src/components/home still contains files.");
}

const routePath = path.join(root, "src/app/page.tsx");

if (!fs.existsSync(routePath)) {
  fail("Homepage route src/app/page.tsx is missing.");
}

const routeContent = fs.readFileSync(routePath, "utf8");

if (
  !routeContent.includes(
    '@/features/f02_home_discovery/HomeDiscoveryPage',
  )
) {
  fail("Homepage route is not connected to F02.");
}

const sourceFiles = walk(path.join(root, "src")).filter((file) =>
  /\.(ts|tsx|js|jsx)$/.test(file),
);

const importPattern =
  /\bfrom\s+["']([^"']+)["']|^\s*import\s+["']([^"']+)["']/gm;

const extensions = [".ts", ".tsx", ".js", ".jsx", ".css", ".json"];

for (const file of sourceFiles) {
  const content = fs.readFileSync(file, "utf8");

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

console.log("");
console.log("===============================================");
console.log("F02 HOME DISCOVERY CONTRACT = PASS");
console.log("43 COMPONENTS               = PASS");
console.log("43 CSS MODULES               = PASS");
console.log("FEATURE ROUTE COMPOSITION    = PASS");
console.log("LEGACY DIRECTORY CLEANUP     = PASS");
console.log("RELATIVE IMPORTS             = PASS");
console.log("===============================================");
