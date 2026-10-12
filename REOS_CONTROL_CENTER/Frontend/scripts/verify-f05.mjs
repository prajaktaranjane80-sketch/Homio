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
const catalog = read("src/features/f05_project/project-preview-catalog.ts");
const route = read("src/app/project/[projectId]/page.tsx");
const actions = read("src/features/f05_project/ProjectActions.tsx");
const gallery = read("src/features/f05_project/ProjectGallery.tsx");
const inventory = read("src/features/f05_project/ProjectInventory.tsx");
const nextStep = read("src/features/f05_project/ProjectNextStep.tsx");
const errorRoute = read("src/app/project/[projectId]/error.tsx");

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

assert(
  catalog.includes("getProjectPreview") &&
    catalog.includes("PROJECT_PREVIEW_IDS"),
  "Project catalogue must reuse the existing F05 data adapter.",
);

assert(
  route.includes("getProjectPreview") &&
    route.includes("notFound") &&
    route.includes("generateMetadata") &&
    route.includes("canonical"),
  "Project route, unavailable handling or SEO metadata is incomplete.",
);

assert(
  errorRoute.includes("reset"),
  "Project route error recovery is missing.",
);

assert(
  data.includes("verified: false") &&
    data.includes("Experience preview"),
  "Preview project data must be explicitly non-authoritative.",
);

assert(
  actions.includes("navigator.share") &&
    actions.includes("temporary experience controls"),
  "Project sharing and temporary save/compare disclosure are missing.",
);

assert(
  gallery.includes("Project media shown here is experience-preview content") &&
    gallery.includes("not connected"),
  "Project media must be clearly marked as a preview placeholder.",
);

assert(
  inventory.includes("Open property") &&
    inventory.includes("Project preview opportunities") &&
    inventory.includes("not asserted"),
  "Project inventory must disclose preview status and keep only supplied property links.",
);

assert(
  nextStep.includes("Continue project discovery") &&
    nextStep.includes("/search?intent=projects"),
  "Project continuation must lead to the Projects search intent.",
);

assert(
  page.includes("#inventory"),
  "Project page inventory context anchor is missing.",
);

for (const forbidden of forbiddenRuntimeReferences) {
  for (const [name, content] of [
    ["ProjectPage.tsx", page],
    ["project route", route],
    ["ProjectActions.tsx", actions],
    ["ProjectInventory.tsx", inventory],
    ["ProjectNextStep.tsx", nextStep],
    ["error route", errorRoute],
  ]) {
    assert(
      !content.includes(forbidden),
      `Forbidden runtime reference in ${name}: ${forbidden}`,
    );
  }
}

console.log("F05 PROJECT & COLLECTION CONTRACT GATE = PASS");
console.log(`FILES VERIFIED = ${requiredFiles.length}`);
console.log("PROJECT CATALOGUE + ROUTE = PASS");
console.log("SEO + NOT-FOUND + ERROR RECOVERY = PASS");
console.log("PROJECT MEDIA PREVIEW DISCLOSURE = PASS");
console.log("INVENTORY DOES NOT CLAIM LIVE AVAILABILITY = PASS");
console.log("PROPERTY LINK BOUNDARY = PASS");
console.log("PROJECT DISCOVERY SEARCH DESTINATION = PASS");
console.log("NO STATE.JSON RUNTIME = PASS");
console.log("NO ACRL RUNTIME = PASS");
