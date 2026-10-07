import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const frontendRoot = path.resolve(__dirname, "..");

const requiredFiles = [
  "src/app/property/[propertyId]/page.tsx",
  "src/app/property/[propertyId]/loading.tsx",
  "src/app/property/[propertyId]/loading.module.css",
  "src/app/property/[propertyId]/not-found.tsx",
  "src/app/property/[propertyId]/error.tsx",
  "src/app/property/[propertyId]/error.module.css",

  "src/features/f04_property/README.md",
  "src/features/f04_property/PropertyAI.tsx",
  "src/features/f04_property/PropertyAI.module.css",
  "src/features/f04_property/PropertyActionBar.tsx",
  "src/features/f04_property/PropertyActionBar.module.css",
  "src/features/f04_property/PropertyAmenities.tsx",
  "src/features/f04_property/PropertyAmenities.module.css",
  "src/features/f04_property/PropertyDetails.tsx",
  "src/features/f04_property/PropertyDetails.module.css",
  "src/features/f04_property/PropertyDisclosure.tsx",
  "src/features/f04_property/PropertyDisclosure.module.css",
  "src/features/f04_property/PropertyFacts.tsx",
  "src/features/f04_property/PropertyFacts.module.css",
  "src/features/f04_property/PropertyGallery.tsx",
  "src/features/f04_property/PropertyGallery.module.css",
  "src/features/f04_property/PropertyLocation.tsx",
  "src/features/f04_property/PropertyLocation.module.css",
  "src/features/f04_property/PropertyNextStep.tsx",
  "src/features/f04_property/PropertyNextStep.module.css",
  "src/features/f04_property/PropertyPage.tsx",
  "src/features/f04_property/PropertyPage.module.css",
  "src/features/f04_property/PropertyProjectContext.tsx",
  "src/features/f04_property/PropertyProjectContext.module.css",
  "src/features/f04_property/PropertySummary.tsx",
  "src/features/f04_property/PropertySummary.module.css",
  "src/features/f04_property/PropertyTrust.tsx",
  "src/features/f04_property/PropertyTrust.module.css",
  "src/features/f04_property/PropertyUnavailable.tsx",
  "src/features/f04_property/PropertyUnavailable.module.css",
  "src/features/f04_property/SimilarProperties.tsx",
  "src/features/f04_property/SimilarProperties.module.css",
  "src/features/f04_property/property.data.ts",
  "src/features/f04_property/property.types.ts",
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
    `Missing required F04 file: ${relativePath}`,
  );
}

const propertyPage = read("src/features/f04_property/PropertyPage.tsx");
const propertyData = read("src/features/f04_property/property.data.ts");
const route = read("src/app/property/[propertyId]/page.tsx");
const pageCss = read(
  "src/features/f04_property/PropertyPage.module.css",
);
const errorRoute = read(
  "src/app/property/[propertyId]/error.tsx",
);

for (const component of [
  "PropertyGallery",
  "PropertySummary",
  "PropertyFacts",
  "PropertyDetails",
  "PropertyProjectContext",
  "PropertyAmenities",
  "PropertyLocation",
  "PropertyTrust",
  "PropertyDisclosure",
  "PropertyAI",
  "SimilarProperties",
  "PropertyNextStep",
]) {
  assert(
    propertyPage.includes(component),
    `PropertyPage is not wired to ${component}.`,
  );
}

assert(
  !propertyPage.includes('className={styles.ai}'),
  "Legacy duplicate AI section remains in PropertyPage.",
);

assert(
  !propertyPage.includes("PropertyUnavailable"),
  "PropertyUnavailable must not be an unused PropertyPage import.",
);

assert(
  route.includes("getPropertyPreview"),
  "Property route preview adapter is missing.",
);

assert(
  route.includes("notFound"),
  "Property route does not fail safely for unavailable references.",
);

assert(
  route.includes("generateMetadata"),
  "Property route metadata is missing.",
);

assert(
  route.includes("canonical"),
  "Property route canonical metadata is missing.",
);

assert(
  errorRoute.includes("reset"),
  "Property route error recovery is missing.",
);

assert(
  propertyData.includes("verified: false"),
  "Preview property data must not manufacture verification.",
);

assert(
  propertyData.includes("Experience preview"),
  "Preview property data must be clearly identified.",
);

assert(
  !pageCss.includes(".ai"),
  "Legacy AI styling remains in PropertyPage.module.css.",
);

for (const forbidden of forbiddenRuntimeReferences) {
  assert(
    !propertyPage.includes(forbidden),
    `Forbidden runtime reference in PropertyPage.tsx: ${forbidden}`,
  );

  assert(
    !route.includes(forbidden),
    `Forbidden runtime reference in property route: ${forbidden}`,
  );

  assert(
    !errorRoute.includes(forbidden),
    `Forbidden runtime reference in property error route: ${forbidden}`,
  );
}

console.log("F04 PROPERTY EXPERIENCE = PASS");
console.log(`FILES VERIFIED = ${requiredFiles.length}`);
console.log("PROPERTY ROUTE = PASS");
console.log("SEO METADATA = PASS");
console.log("PROPERTY COMPOSITION = PASS");
console.log("FACTS + DETAILS = PASS");
console.log("PROJECT + LOCATION = PASS");
console.log("TRUST + DISCLOSURE = PASS");
console.log("AI + SIMILAR DISCOVERY = PASS");
console.log("ENQUIRY + VISIT ENTRY = PASS");
console.log("LOADING + NOT FOUND = PASS");
console.log("ERROR RECOVERY = PASS");
console.log("PREVIEW DATA NON-AUTHORITATIVE = PASS");
console.log("NO ACRL RUNTIME = PASS");
console.log("NO STATE.JSON RUNTIME = PASS");
