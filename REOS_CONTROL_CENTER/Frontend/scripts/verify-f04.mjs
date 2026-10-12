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

const route = read("src/app/property/[propertyId]/page.tsx");
const loading = read("src/app/property/[propertyId]/loading.tsx");
const notFoundRoute = read(
  "src/app/property/[propertyId]/not-found.tsx",
);
const errorRoute = read("src/app/property/[propertyId]/error.tsx");

const propertyPage = read("src/features/f04_property/PropertyPage.tsx");
const propertyData = read("src/features/f04_property/property.data.ts");
const propertyCatalog = read(
  "src/features/f04_property/property-preview-catalog.ts",
);
const projectData = read("src/features/f05_project/project.data.ts");

const propertyGallery = read(
  "src/features/f04_property/PropertyGallery.tsx",
);
const propertySummary = read(
  "src/features/f04_property/PropertySummary.tsx",
);
const propertyFacts = read(
  "src/features/f04_property/PropertyFacts.tsx",
);
const propertyActionBar = read(
  "src/features/f04_property/PropertyActionBar.tsx",
);
const propertyActionBarCss = read(
  "src/features/f04_property/PropertyActionBar.module.css",
);
const propertyAI = read("src/features/f04_property/PropertyAI.tsx");
const propertyAmenities = read(
  "src/features/f04_property/PropertyAmenities.tsx",
);
const propertyDetails = read(
  "src/features/f04_property/PropertyDetails.tsx",
);
const propertyDisclosure = read(
  "src/features/f04_property/PropertyDisclosure.tsx",
);
const propertyTrust = read(
  "src/features/f04_property/PropertyTrust.tsx",
);
const propertyLocation = read(
  "src/features/f04_property/PropertyLocation.tsx",
);
const propertyLocationCss = read(
  "src/features/f04_property/PropertyLocation.module.css",
);
const propertyNextStep = read(
  "src/features/f04_property/PropertyNextStep.tsx",
);
const propertyNextStepCss = read(
  "src/features/f04_property/PropertyNextStep.module.css",
);
const propertyProjectContext = read(
  "src/features/f04_property/PropertyProjectContext.tsx",
);
const similarProperties = read(
  "src/features/f04_property/SimilarProperties.tsx",
);
const similarPropertiesCss = read(
  "src/features/f04_property/SimilarProperties.module.css",
);

const normalizedRoute = normalizeWhitespace(route);
const normalizedGallery = normalizeWhitespace(propertyGallery);
const normalizedActionBar = normalizeWhitespace(propertyActionBar);
const normalizedNextStep = normalizeWhitespace(propertyNextStep);
const normalizedAmenities = normalizeWhitespace(propertyAmenities);
const normalizedDetails = normalizeWhitespace(propertyDetails);
const normalizedLocation = normalizeWhitespace(propertyLocation);
const normalizedDisclosure = normalizeWhitespace(propertyDisclosure);
const normalizedTrust = normalizeWhitespace(propertyTrust);

/*
 * Route and metadata integrity:
 * these current records are experience previews, not published listings.
 */
assert(
  route.includes("getPropertyPreview") &&
    route.includes("notFound") &&
    route.includes("generateMetadata"),
  "Property route must resolve previews and handle unavailable IDs.",
);

assert(
  normalizedRoute.includes("index: false") &&
    normalizedRoute.includes("follow: true") &&
    normalizedRoute.includes("Experience Preview") &&
    !normalizedRoute.includes("canonical:"),
  "Unverified preview metadata must remain noindex and must not advertise a canonical URL.",
);

assert(
  notFoundRoute.includes("PropertyUnavailable") &&
    notFoundRoute.includes("couldn't find this property"),
  "The unavailable route must render a specific not-found experience.",
);

assert(
  loading.includes("PropertyLoading"),
  "Property route loading UI is missing.",
);

assert(
  errorRoute.includes("reset") &&
    errorRoute.includes("Return to search"),
  "Property route must provide error recovery and a search return path.",
);

/*
 * Composition and international navigation:
 * property pages must not contain locality-specific hard-coded routes.
 */
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
  propertyPage.includes("buildSearchHref") &&
    propertyPage.includes("new URLSearchParams()") &&
    propertyPage.includes("property.city") &&
    propertyPage.includes("property.country") &&
    propertyPage.includes("property.locality") &&
    !propertyPage.includes("Kalyani Nagar") &&
    !propertyPage.includes("city=Pune"),
  "Related discovery must be derived from the current property, not a hard-coded city.",
);

assert(
  propertyPage.includes("key={property.id}") &&
    propertyPage.includes('aria-current="page"'),
  "The property gallery must reset per record and the breadcrumb must identify the current page.",
);

assert(
  !propertyPage.includes("PropertyUnavailable"),
  "The normal PropertyPage must not import the standalone unavailable state.",
);

/*
 * Preview disclosure and non-authoritative sample data.
 */
assert(
  propertyData.includes("verified: false") &&
    propertyData.includes("Experience preview") &&
    propertyData.includes("Verification pending"),
  "Preview records must remain explicitly non-authoritative.",
);

assert(
  propertySummary.includes("styles.previewBadge") &&
    propertySummary.includes("verificationLabel"),
  "The property summary must visibly distinguish unverified previews.",
);

assert(
  propertyFacts.includes("Bedrooms") &&
    !propertyFacts.includes("BHK"),
  "Property facts must use internationally understandable bedroom terminology.",
);

assert(
  normalizedTrust.includes("verificationLabel") &&
    normalizedTrust.includes("not been verified"),
  "Trust status must explain preview verification honestly.",
);

assert(
  normalizedDisclosure.includes("verificationLabel") &&
    normalizedDisclosure.includes("not been verified") &&
    normalizedDisclosure.includes("Pricing and availability"),
  "Disclosure must distinguish verification state and illustrative property information.",
);

assert(
  normalizedAmenities.includes("amenities.filter") &&
    normalizedAmenities.includes("Amenity information not supplied") &&
    normalizedAmenities.includes("will not invent facilities"),
  "Placeholder amenities must be filtered and replaced with an explicit empty state.",
);

assert(
  normalizedDetails.includes("highlights.filter") &&
    normalizedDetails.includes("No property highlights are supplied") &&
    normalizedDetails.includes("Not supplied in this preview"),
  "Placeholder highlights and absent project associations must not be presented as facts.",
);

assert(
  normalizedGallery.includes("Preview placeholders only") &&
    normalizedGallery.includes("not supplied"),
  "Property gallery must disclose missing actual media.",
);

assert(
  normalizedLocation.includes("nearby.filter") &&
    normalizedLocation.includes("No proximity estimates have been invented") &&
    normalizedLocation.includes("authoritative coordinates") &&
    propertyLocationCss.includes(".nearbyEmpty"),
  "Location must not fabricate coordinates, nearby places or distances.",
);

assert(
  propertyAI.includes("AI NOT CONNECTED") &&
    propertyAI.includes("No AI request was sent"),
  "The AI entry point must not imply a generated answer exists.",
);

/*
 * Action targets must be distinct. Enquiry and visit controls stay disabled
 * until an approved form and submission capability exist.
 */
assert(
  normalizedActionBar.includes('href="#property-next-step-enquiry"') &&
    normalizedActionBar.includes('href="#property-next-step-visit"') &&
    normalizedActionBar.includes("navigator.share") &&
    normalizedActionBar.includes("temporary"),
  "Property actions must use distinct targets, safe sharing and temporary-state disclosure.",
);

assert(
  propertyActionBarCss.includes(":focus-visible") &&
    !propertyActionBarCss.includes("position: sticky"),
  "Property actions must have visible keyboard focus and not rely on a misleading local sticky bar.",
);

assert(
  normalizedNextStep.includes('id="property-next-step-enquiry"') &&
    normalizedNextStep.includes('id="property-next-step-visit"') &&
    normalizedNextStep.includes("disabled") &&
    normalizedNextStep.includes("No request has been created or sent") &&
    propertyNextStepCss.includes(".options") &&
    propertyNextStepCss.includes(".option"),
  "Enquiry and visit capabilities must have separate targets and remain safely disabled.",
);

/*
 * Project associations and similar-property matching.
 */
assert(
  propertyProjectContext.includes("Not supplied in preview") &&
    propertyProjectContext.includes("property.projectId") &&
    projectData.includes('id: "homio-kalyani-residences-001"'),
  "Project context must disclose missing builder data and use a resolvable project destination.",
);

const catalogBlock = propertyCatalog.match(
  /const PROPERTY_PREVIEW_IDS = \[([\s\S]*?)\] as const;/,
);

assert(
  catalogBlock !== null,
  "The shared property preview catalogue has no readable ID list.",
);

const catalogIds = [
  ...catalogBlock[1].matchAll(/"([^"]+)"/g),
].map((match) => match[1]);

assert(
  catalogIds.length > 0 &&
    new Set(catalogIds).size === catalogIds.length,
  "The property preview catalogue must have unique IDs.",
);

for (const id of catalogIds) {
  assert(
    propertyData.includes(`id: "${id}"`),
    `Property catalogue ID does not resolve through property.data.ts: ${id}`,
  );
}

const linkedProjectIds = [
  ...propertyData.matchAll(/\bprojectId:\s*"([^"]+)"/g),
].map((match) => match[1]);

for (const projectId of linkedProjectIds) {
  assert(
    projectData.includes(`id: "${projectId}"`),
    `Property refers to an unresolved project preview ID: ${projectId}`,
  );
}

assert(
  similarProperties.includes("getAllPropertyPreviews") &&
    similarProperties.includes("item.country") &&
    similarProperties.includes("sameLocality") &&
    similarProperties.includes("propertyType") &&
    similarProperties.includes("item.id !== property.id"),
  "Similar property suggestions must stay in the same country/city and rank relevant records first.",
);

assert(
  similarPropertiesCss.includes(".view") &&
    !similarPropertiesCss.includes(".body button"),
  "Similar-property link styling must match the actual Link element.",
);

/*
 * F04 remains a presentation layer. No backend control-plane state,
 * architecture file or ACRL runtime may be loaded by this feature.
 */
const featureSources = [
  ["property route", route],
  ["PropertyPage.tsx", propertyPage],
  ["property.data.ts", propertyData],
  ["PropertySummary.tsx", propertySummary],
  ["PropertyActionBar.tsx", propertyActionBar],
  ["PropertyAI.tsx", propertyAI],
  ["PropertyAmenities.tsx", propertyAmenities],
  ["PropertyDetails.tsx", propertyDetails],
  ["PropertyDisclosure.tsx", propertyDisclosure],
  ["PropertyTrust.tsx", propertyTrust],
  ["PropertyLocation.tsx", propertyLocation],
  ["PropertyNextStep.tsx", propertyNextStep],
  ["PropertyProjectContext.tsx", propertyProjectContext],
  ["SimilarProperties.tsx", similarProperties],
];

for (const forbidden of forbiddenRuntimeReferences) {
  for (const [name, content] of featureSources) {
    assert(
      !content.includes(forbidden),
      `Forbidden runtime reference in ${name}: ${forbidden}`,
    );
  }
}

console.log("F04 PROPERTY CONTRACT GATE = PASS");
console.log(`FILES VERIFIED = ${requiredFiles.length}`);
console.log("ROUTE + PREVIEW SEO BOUNDARY = PASS");
console.log("DYNAMIC INTERNATIONAL DISCOVERY LINKS = PASS");
console.log("UNVERIFIED PREVIEW DISCLOSURE = PASS");
console.log("EMPTY-STATE DATA SAFETY = PASS");
console.log("MEDIA + LOCATION DISCLOSURE = PASS");
console.log("AI + ENQUIRY + VISIT CAPABILITY BOUNDARIES = PASS");
console.log("PROJECT REFERENCE INTEGRITY = PASS");
console.log("SIMILAR PROPERTY RELEVANCE = PASS");
console.log("NO STATE.JSON RUNTIME = PASS");
console.log("NO ACRL RUNTIME = PASS");
