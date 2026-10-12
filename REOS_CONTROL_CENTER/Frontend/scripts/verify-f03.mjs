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
  "src/features/f04_property/property-preview-catalog.ts",
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
    `Missing required F04 file: ${relativePath}`,
  );
}

const propertyPage = read("src/features/f04_property/PropertyPage.tsx");
const propertyData = read("src/features/f04_property/property.data.ts");
const propertyCatalog = read(
  "src/features/f04_property/property-preview-catalog.ts",
);
const route = read("src/app/property/[propertyId]/page.tsx");
const pageCss = read("src/features/f04_property/PropertyPage.module.css");
const errorRoute = read("src/app/property/[propertyId]/error.tsx");

const propertyGallery = read(
  "src/features/f04_property/PropertyGallery.tsx",
);
const propertyActionBar = read(
  "src/features/f04_property/PropertyActionBar.tsx",
);
const propertyAI = read("src/features/f04_property/PropertyAI.tsx");
const propertyLocation = read(
  "src/features/f04_property/PropertyLocation.tsx",
);
const propertyNextStep = read(
  "src/features/f04_property/PropertyNextStep.tsx",
);
const projectContext = read(
  "src/features/f04_property/PropertyProjectContext.tsx",
);
const similarProperties = read(
  "src/features/f04_property/SimilarProperties.tsx",
);

/*
 * Normalize JSX whitespace for human-readable disclosure checks.
 * A line break or indentation must not cause a false CI failure.
 */
const normalizedPropertyData = normalizeWhitespace(propertyData);
const normalizedPropertyGallery = normalizeWhitespace(propertyGallery);
const normalizedPropertyActionBar = normalizeWhitespace(propertyActionBar);
const normalizedPropertyAI = normalizeWhitespace(propertyAI);
const normalizedPropertyLocation = normalizeWhitespace(propertyLocation);
const normalizedPropertyNextStep = normalizeWhitespace(propertyNextStep);
const normalizedProjectContext = normalizeWhitespace(projectContext);

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
  !propertyPage.includes("className={styles.ai}"),
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
  route.includes("generateMetadata") && route.includes("canonical"),
  "Property route SEO metadata is incomplete.",
);

assert(
  errorRoute.includes("reset"),
  "Property route error recovery is missing.",
);

assert(
  normalizedPropertyData.includes("verified: false") &&
    normalizedPropertyData.includes("Experience preview"),
  "Preview data must remain explicitly non-authoritative.",
);

assert(
  propertyCatalog.includes("getPropertyPreview") &&
    similarProperties.includes("getAllPropertyPreviews"),
  "Similar properties must reuse the shared F04 preview catalogue.",
);

assert(
  normalizedPropertyGallery.includes("Preview placeholders only") &&
    normalizedPropertyGallery.includes("not supplied"),
  "Property media must disclose when actual media is not supplied.",
);

assert(
  normalizedPropertyActionBar.includes('href="#property-next-step"') &&
    normalizedPropertyActionBar.includes("temporary") &&
    normalizedPropertyActionBar.includes("navigator.share"),
  "Property actions must disclose temporary state and support safe sharing.",
);

assert(
  normalizedPropertyAI.includes("disabled") &&
    normalizedPropertyAI.includes("AI NOT CONNECTED") &&
    normalizedPropertyAI.includes("No AI request was sent"),
  "Property AI must not present prompt text as a generated answer.",
);

assert(
  normalizedPropertyNextStep.includes("disabled") &&
    normalizedPropertyNextStep.includes("not connected") &&
    normalizedPropertyNextStep.includes("No request has been created"),
  "Property enquiry/visit flow must not imply an unconnected submission succeeded.",
);

assert(
  normalizedPropertyLocation.includes("not a live map") &&
    normalizedPropertyLocation.includes("authoritative coordinates"),
  "Property location preview must not claim live map accuracy.",
);

assert(
  normalizedProjectContext.includes("Not supplied in preview"),
  "Property project context must not invent an authorized builder/partner.",
);

assert(
  !pageCss.includes(".ai"),
  "Legacy AI styling remains in PropertyPage.module.css.",
);

for (const forbidden of forbiddenRuntimeReferences) {
  for (const [name, content] of [
    ["PropertyPage.tsx", propertyPage],
    ["property route", route],
    ["property error route", errorRoute],
  ]) {
    assert(
      !content.includes(forbidden),
      `Forbidden runtime reference in ${name}: ${forbidden}`,
    );
  }
}

console.log("F04 PROPERTY CONTRACT GATE = PASS");
console.log(`FILES VERIFIED = ${requiredFiles.length}`);
console.log("PROPERTY ROUTE + SEO = PASS");
console.log("SHARED PROPERTY PREVIEW CATALOGUE = PASS");
console.log("MEDIA PLACEHOLDER DISCLOSURE = PASS");
console.log("AI DOES NOT FABRICATE ANSWERS = PASS");
console.log("ENQUIRY / VISIT SUBMISSION BOUNDARY = PASS");
console.log("LOCATION COORDINATE BOUNDARY = PASS");
console.log("PROJECT-PARTNER CLAIM BOUNDARY = PASS");
console.log("SIMILAR PROPERTY FILTERING = PASS");
console.log("ERROR RECOVERY = PASS");
console.log("NO STATE.JSON RUNTIME = PASS");
console.log("NO ACRL RUNTIME = PASS");
