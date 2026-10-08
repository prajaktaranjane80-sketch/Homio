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
  return fs.readFileSync(
    absolute(relativePath),
    "utf8",
  );
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

const page = read(
  "src/features/f05_project/ProjectPage.tsx",
);

const data = read(
  "src/features/f05_project/project.data.ts",
);

const route = read(
  "src/app/project/[projectId]/page.tsx",
);

const actions = read(
  "src/features/f05_project/ProjectActions.tsx",
);

const inventory = read(
  "src/features/f05_project/ProjectInventory.tsx",
);

const nextStep = read(
  "src/features/f05_project/ProjectNextStep.tsx",
);

const errorRoute = read(
  "src/app/project/[projectId]/error.tsx",
);

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
  route.includes("getProjectPreview"),
  "Project route preview adapter is missing.",
);

assert(
  route.includes("notFound"),
  "Project route does not fail safely for unavailable references.",
);

assert(
  route.includes("generateMetadata"),
  "Project route metadata is missing.",
);

assert(
  route.includes("canonical"),
  "Project route canonical metadata is missing.",
);

assert(
  errorRoute.includes("reset"),
  "Project route error recovery is missing.",
);

assert(
  data.includes("verified: false"),
  "Preview project data must not manufacture verification.",
);

assert(
  data.includes("Experience preview"),
  "Preview project data must be explicitly identified.",
);

assert(
  actions.includes("navigator.share"),
  "Project share presentation is missing.",
);

assert(
  inventory.includes("Open property"),
  "Project inventory to property journey is missing.",
);

assert(
  nextStep.includes("Continue project discovery"),
  "Project continuation action is missing.",
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

console.log(
  "F05 PROJECT & COLLECTION EXPERIENCE = PASS",
);
console.log(
  `FILES VERIFIED = ${requiredFiles.length}`,
);
console.log("PROJECT ROUTE = PASS");
console.log("SEO METADATA = PASS");
console.log("PROJECT COMPOSITION = PASS");
console.log("PROJECT SUMMARY = PASS");
console.log("PROJECT FACTS = PASS");
console.log("INVENTORY SUMMARY = PASS");
console.log("INVENTORY → PROPERTY = PASS");
console.log("PROJECT FEATURES = PASS");
console.log("LOCATION CONTEXT = PASS");
console.log("TRUST STATE = PASS");
console.log("RELATED DISCOVERY = PASS");
console.log("NEXT STEP = PASS");
console.log("LOADING + NOT FOUND = PASS");
console.log("ERROR RECOVERY = PASS");
console.log(
  "PREVIEW DATA NON-AUTHORITATIVE = PASS",
);
console.log("NO ACRL RUNTIME = PASS");
console.log("NO STATE.JSON RUNTIME = PASS");
