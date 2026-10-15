import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(scriptDirectory, "..");

function absolute(relativePath) {
  return path.join(frontendRoot, relativePath);
}

function read(relativePath) {
  const targetPath = absolute(relativePath);

  assert.ok(
    fs.existsSync(targetPath),
    `Required file is missing: ${relativePath}`,
  );

  return fs.readFileSync(targetPath, "utf8");
}

const f09Root = "src/features/f09_enquiry_visit";

const requiredModules = [
  "README.md",
  "EnquiryShell.tsx",
  "EnquiryContactDetails.tsx",
  "EnquiryContactPreference.tsx",
  "EnquiryQualification.tsx",
  "PropertyEnquiryForm.tsx",
  "ProjectEnquiryForm.tsx",
  "GeneralEnquiryForm.tsx",
  "EnquiryConfirmation.tsx",
  "EnquiryStatus.tsx",
  "EnquiryHistory.tsx",
  "VisitRequestForm.tsx",
  "VisitDateTimeSelector.tsx",
  "VisitConfirmation.tsx",
  "VisitStatus.tsx",
  "VisitReschedule.tsx",
  "VisitCancel.tsx",
  "VisitFollowUp.tsx",
  "VisitHistory.tsx",
  "enquiry.constants.ts",
  "enquiry.types.ts",
  "visit.types.ts",
  "EnquiryWorkspace.module.css",
];

for (const moduleName of requiredModules) {
  read(`${f09Root}/${moduleName}`);
}

const css = read(`${f09Root}/EnquiryWorkspace.module.css`);

const cssOpenBraces = (css.match(/{/g) ?? []).length;
const cssCloseBraces = (css.match(/}/g) ?? []).length;

assert.equal(cssOpenBraces, cssCloseBraces, "F09 CSS has unmatched braces.");
assert.ok(css.trimEnd().endsWith("}"), "F09 CSS appears truncated.");

const styleNames = new Set();
const f09Files = fs.readdirSync(absolute(f09Root));

for (const fileName of f09Files.filter((name) => /\.(tsx|ts)$/.test(name))) {
  const source = read(`${f09Root}/${fileName}`);

  for (const match of source.matchAll(/styles\.([A-Za-z_][A-Za-z0-9_]*)/g)) {
    styleNames.add(match[1]);
  }
}

const missingStyles = [...styleNames].filter((name) => {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  return !new RegExp(`\\.${escaped}(?=[\\s.:#[,>+~{])`).test(css);
});

assert.deepEqual(
  missingStyles,
  [],
  `F09 CSS classes are missing: ${missingStyles.join(", ")}`,
);

const constants = read(`${f09Root}/enquiry.constants.ts`);

assert.match(constants, /ENQUIRY_SERVICE_CONNECTED\s*=\s*false/);
assert.match(constants, /VISIT_SCHEDULING_SERVICE_CONNECTED\s*=\s*false/);

const enquiryRoute = read("src/app/enquiry/page.tsx");

assert.match(enquiryRoute, /getPropertyPreview/);
assert.match(enquiryRoute, /getProjectPreview/);
assert.match(enquiryRoute, /requestedMode\s*===\s*"visit"/);
assert.match(enquiryRoute, /if\s*\(!property\)\s*notFound\(\)/);
assert.match(enquiryRoute, /if\s*\(!project\)\s*notFound\(\)/);

const propertyNextStep = read("src/features/f04_property/PropertyNextStep.tsx");

assert.match(propertyNextStep, /\/enquiry\?kind=property/);
assert.match(propertyNextStep, /&mode=visit/);
assert.match(propertyNextStep, /<Link/);
assert.doesNotMatch(propertyNextStep, /<button[^>]*disabled/);

assert.match(
  read("src/features/f04_property/PropertyPage.tsx"),
  /<PropertyNextStep property=\{property\}\s*\/>/,
);

const projectNextStep = read("src/features/f05_project/ProjectNextStep.tsx");

assert.match(projectNextStep, /\/enquiry\?kind=project/);
assert.match(projectNextStep, /&mode=visit/);
assert.match(projectNextStep, /<Link/);

const shell = read(`${f09Root}/EnquiryShell.tsx`);

assert.match(shell, /initialMode/);
assert.match(shell, /aria-pressed=/);
assert.match(shell, /ENQUIRY_SERVICE_NOTICE/);
assert.match(shell, /VISIT_SERVICE_NOTICE/);

const packageJson = JSON.parse(read("package.json"));

assert.equal(
  packageJson.scripts["verify:f09"],
  "node ./scripts/verify-f09.mjs",
);

assert.match(packageJson.scripts.verify, /npm run verify:f09/);

console.log(
  `F09 verification passed: ${requiredModules.length} required modules, ` +
    `${styleNames.size} CSS-module selectors, target-aware enquiry/visit ` +
    "entry points, and draft-only service flags.",
);
