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

// Metadata assertions must inspect source code, not explanatory comments.
const routeWithoutComments = route
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .replace(/^\s*\/\/.*$/gm, "");

const normalizedRoute = normalizeWhitespace(routeWithoutComments);

/* PAGE COMPOSITION */
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

/* PROJECT ROUTE AND SEO */
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
  "Unverified project previews must be noindex without a canonical URL.",
);

assert(
  normalizedRoute.includes("not authoritative") &&
    normalizedRoute.includes("openGraph"),
  "Project metadata must disclose preview status and define Open Graph metadata.",
);

assert(
  normalizedRoute.includes("follow: false") &&
    notFoundRoute.includes("ProjectUnavailable"),
  "Unknown project IDs must be non-indexed and render the unavailable state.",
);

assert(
  errorRoute.includes("reset") &&
    errorRoute.includes("Return to search"),
  "Project errors must provide recovery and return navigation.",
);

/* PREVIEW TRUTH AND USER ACTIONS */
assert(
  data.includes("verified: false") &&
    data.includes("Experience preview"),
  "Project preview records must remain explicitly non-authoritative.",
);

assert(
  actions.includes("navigator.share") &&
    actions.includes("temporary experience controls"),
  "Share and temporary save/compare controls must be disclosed.",
);

assert(
  gallery.includes(
    "Project media shown here is experience-preview content",
  ) &&
    gallery.includes("not connected"),
  "Unconnected project media must be disclosed as preview content.",
);

assert(
  inventory.includes("Open property") &&
    inventory.includes("Project preview opportunities") &&
    inventory.includes("not asserted"),
  "Project inventory must disclose preview status and avoid claiming live availability.",
);

assert(
  nextStep.includes("Continue project discovery") &&
    nextStep.includes("/search?intent=projects") &&
    page.includes("#inventory"),
  "Project discovery navigation must use valid destinations and anchors.",
);

assert(
  location.includes("Location preview") &&
    trust.includes("verificationLabel"),
  "Location and trust sections must retain preview and verification context.",
);

/* PROJECT CATALOGUE INTEGRITY */
assert(
  catalog.includes("getProjectPreview") &&
    catalog.includes("PROJECT_PREVIEW_IDS"),
  "Project catalogue must reuse the existing F05 data adapter.",
);

const catalogBlock = catalog.match(
  /const PROJECT_PREVIEW_IDS = \[([\s\S]*?)\] as const;/,
);

assert(
  catalogBlock !== null,
  "Project catalogue must declare its preview ID registry.",
);

const catalogIds = [
  ...catalogBlock[1].matchAll(/"([^"]+)"/g),
].map((match) => match[1]);

assert(
  catalogIds.length > 0 &&
    new Set(catalogIds).size === catalogIds.length,
  "Project catalogue IDs must be non-empty and unique.",
);

for (const id of catalogIds) {
  assert(
    data.includes(`id: "${id}"`),
    `Project catalogue ID does not resolve in project.data.ts: ${id}`,
  );
}

/* RELATED PROJECT REFERENCES */
const relatedBlocks = [
  ...data.matchAll(/relatedProjects:\s*\[([\s\S]*?)\]/g),
].map((match) => match[1]);

const relatedIds = relatedBlocks.flatMap((block) =>
  [...block.matchAll(/id:\s*"([^"]+)"/g)].map(
    (match) => match[1],
  ),
);

for (const id of relatedIds) {
  assert(
    catalogIds.includes(id),
    `Related project reference does not resolve through F05 catalogue: ${id}`,
  );
}

assert(
  relatedProjects.includes('href={`/project/${item.id}`}') &&
    relatedProjects.includes("project.relatedProjects.map"),
  "Related-project links must use supplied project references.",
);

/* PROJECT INVENTORY PROPERTY LINKS */
const propertyIds = [
  ...data.matchAll(/href:\s*"\/property\/([^"]+)"/g),
].map((match) => match[1]);

for (const propertyId of propertyIds) {
  assert(
    propertyData.includes(`id: "${propertyId}"`),
    `Project inventory refers to an unresolved F04 property ID: ${propertyId}`,
  );
}

/* FRONTEND / BACKEND BOUNDARY */
const featureSources = [
  ["ProjectPage.tsx", page],
  ["project route", route],
  ["project.data.ts", data],
  ["project-preview-catalog.ts", catalog],
  ["ProjectActions.tsx", actions],
  ["ProjectGallery.tsx", gallery],
  ["ProjectInventory.tsx", inventory],
  ["ProjectNextStep.tsx", nextStep],
  ["ProjectLocation.tsx", location],
  ["ProjectTrust.tsx", trust],
  ["RelatedProjects.tsx", relatedProjects],
  ["project error route", errorRoute],
];

for (const forbidden of forbiddenRuntimeReferences) {
  for (const [name, content] of featureSources) {
    assert(
      !content.includes(forbidden),
      `Forbidden runtime reference in ${name}: ${forbidden}`,
    );
  }
}

console.log("F05 PROJECT & COLLECTION CONTRACT GATE = PASS");
console.log(`FILES VERIFIED = ${requiredFiles.length}`);
console.log("PROJECT CATALOGUE + ROUTE = PASS");
console.log("PREVIEW SEO + NOT-FOUND + ERROR RECOVERY = PASS");
console.log("UNVERIFIED PROJECTS ARE NON-INDEXED = PASS");
console.log("PROJECT MEDIA PREVIEW DISCLOSURE = PASS");
console.log("INVENTORY DOES NOT CLAIM LIVE AVAILABILITY = PASS");
console.log("RELATED PROJECT REFERENCES RESOLVE = PASS");
console.log("PROPERTY REFERENCES RESOLVE THROUGH F04 = PASS");
console.log("PROJECT DISCOVERY SEARCH DESTINATION = PASS");
console.log("NO STATE.JSON RUNTIME = PASS");
console.log("NO ACRL RUNTIME = PASS");
