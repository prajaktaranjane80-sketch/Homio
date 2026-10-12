import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, "..");

const requiredFiles = [
  "src/app/project/[projectId]/page.tsx",
  "src/app/project/[projectId]/loading.tsx",
  "src/app/project/[projectId]/loading.module.css",
  "src/app/project/[projectId]/not-found.tsx",
  "src/app/project/[projectId]/error.tsx",
  "src/app/project/[projectId]/error.module.css",
  "src/features/f05_project/README.md",
  "src/features/f05_project/ProjectPage.tsx",
  "src/features/f05_project/ProjectPage.module.css",
  "src/features/f05_project/ProjectActions.tsx",
  "src/features/f05_project/ProjectActions.module.css",
  "src/features/f05_project/ProjectGallery.tsx",
  "src/features/f05_project/ProjectGallery.module.css",
  "src/features/f05_project/ProjectSummary.tsx",
  "src/features/f05_project/ProjectSummary.module.css",
  "src/features/f05_project/ProjectFacts.tsx",
  "src/features/f05_project/ProjectFacts.module.css",
  "src/features/f05_project/ProjectInventorySummary.tsx",
  "src/features/f05_project/ProjectInventorySummary.module.css",
  "src/features/f05_project/ProjectInventory.tsx",
  "src/features/f05_project/ProjectInventory.module.css",
  "src/features/f05_project/ProjectAmenities.tsx",
  "src/features/f05_project/ProjectAmenities.module.css",
  "src/features/f05_project/ProjectLocation.tsx",
  "src/features/f05_project/ProjectLocation.module.css",
  "src/features/f05_project/ProjectTrust.tsx",
  "src/features/f05_project/ProjectTrust.module.css",
  "src/features/f05_project/RelatedProjects.tsx",
  "src/features/f05_project/RelatedProjects.module.css",
  "src/features/f05_project/ProjectNextStep.tsx",
  "src/features/f05_project/ProjectNextStep.module.css",
  "src/features/f05_project/ProjectUnavailable.tsx",
  "src/features/f05_project/ProjectUnavailable.module.css",
  "src/features/f05_project/project.types.ts",
  "src/features/f05_project/project.data.ts",
  "src/features/f05_project/project-preview-catalog.ts",
];

const forbiddenRuntimeReferences = [
  "data/state.json",
  "HOMIO_REOS_MASTER_ARCHITECTURE.json",
  "AUTONOMY_ENGINE",
  "ACRL",
];

function absolute(relativePath) {
  return path.join(frontendRoot, relativePath);
}

function read(relativePath) {
  return fs.readFileSync(absolute(relativePath), "utf8");
}

function normalizeWhitespace(value) {
  return value.replace(/\s+/g, " ").trim();
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

for (const relativePath of requiredFiles) {
  assert(
    fs.existsSync(absolute(relativePath)),
    `Missing required F05 file: ${relativePath}`,
  );
}

const page = read("src/features/f05_project/ProjectPage.tsx");
const data = read("src/features/f05_project/project.data.ts");
const catalog = read(
  "src/features/f05_project/project-preview-catalog.ts",
);
const route = read("src/app/project/[projectId]/page.tsx");
const notFoundRoute = read(
  "src/app/project/[projectId]/not-found.tsx",
);
const actions = read("src/features/f05_project/ProjectActions.tsx");
const gallery = read("src/features/f05_project/ProjectGallery.tsx");
const inventory = read("src/features/f05_project/ProjectInventory.tsx");
const nextStep = read("src/features/f05_project/ProjectNextStep.tsx");
const location = read("src/features/f05_project/ProjectLocation.tsx");
const trust = read("src/features/f05_project/ProjectTrust.tsx");
const relatedProjects = read(
  "src/features/f05_project/RelatedProjects.tsx",
);
const errorRoute = read("src/app/project/[projectId]/error.tsx");
const propertyData = read(
  "src/features/f04_property/property.data.ts",
);

// Ignore comments so prose does not decide whether metadata is configured.
const routeWithoutComments = route
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .replace(/^\s*\/\/.*$/gm, "");

const normalizedRoute = normalizeWhitespace(routeWithoutComments);

/*
 * FILE + COMPONENT CONTRACT
 */
for (const component of [
  "ProjectGallery",
  "ProjectSummary",
  "ProjectActions",
  "ProjectFacts",
  "ProjectInventorySummary",
  "ProjectInventory",
  "ProjectAmenities",
  "ProjectLocation",
  "ProjectTrust",
  "RelatedProjects",
  "ProjectNextStep",
]) {
  assert(
    page.includes(component),
    `ProjectPage is not wired to ${component}.`,
  );
}

/*
 * PROJECT ROUTE + PREVIEW SEO SAFETY
 */
assert(
  normalizedRoute.includes("getProjectPreview") &&
    normalizedRoute.includes("notFound") &&
    normalizedRoute.includes("generateMetadata"),
  "Project route must resolve known previews and reject unknown IDs.",
);

assert(
  normalizedRoute.includes("Project Experience Preview") &&
    normalizedRoute.includes("index: false") &&
    normalizedRoute.includes("follow: true") &&
    !/\balternates\s*:/.test(normalizedRoute) &&
    !/\bcanonical\s*:/.test(normalizedRoute),
  "Unverified project previews must be noindex and must not declare a canonical URL.",
);

assert(
  normalizedRoute.includes("not authoritative") &&
    normalizedRoute.includes("openGraph"),
  "Project metadata must disclose preview status and provide coherent share metadata.",
);

assert(
  normalizedRoute.includes("follow: false") &&
    notFoundRoute.includes("ProjectUnavailable"),
  "Unknown project routes must remain non-indexed and render an unavailable state.",
);

assert(
  errorRoute.includes("reset") &&
    errorRoute.includes("Return to search"),
  "Project errors must provide recovery and return navigation.",
);

/*
 * AUTHORITATIVE DATA + PREVIEW DISCLOSURE
 */
assert(
  data.includes("verified: false") &&
    data.includes("Experience preview"),
  "Project preview records must remain explicitly non-authoritative
