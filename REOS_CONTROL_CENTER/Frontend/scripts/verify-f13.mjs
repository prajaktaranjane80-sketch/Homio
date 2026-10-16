
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const feature = path.join(root, "src", "features", "f13_production");

const requiredFiles = [
  "README.md",
  "ResponsiveAudit.tsx",
  "AccessibilityAudit.tsx",
  "SeoMetadata.ts",
  "PerformanceConfig.ts",
  "ImagePolicy.ts",
  "ErrorBoundary.tsx",
  "LoadingBoundary.tsx",
  "EmptyStatePolicy.ts",
  "AnalyticsEvents.ts",
  "ConversionEvents.ts",
  "ProductionGuards.ts",
  "RuntimeChecks.ts",
];

for (const file of requiredFiles) {
  assert.ok(
    fs.existsSync(path.join(feature, file)),
    "F13 required file is missing: " + file,
  );
}

function readFeatureFile(name) {
  return fs.readFileSync(path.join(feature, name), "utf8");
}

const analytics = readFeatureFile("AnalyticsEvents.ts");
assert.match(analytics, /SAFE_PROPERTY_KEYS/);
assert.match(analytics, /SAFE_PROPERTY_KEYS\.has\(key\)/);
assert.match(analytics, /Analytics must never interrupt/i);
assert.doesNotMatch(
  analytics,
  /FORBIDDEN_PROPERTY_KEYS\.has\(normalizedKey\)/,
);

const responsive = readFeatureFile("ResponsiveAudit.tsx");
assert.match(responsive, /mobile:\s*767/);
assert.match(responsive, /tablet:\s*1023/);
assert.match(responsive, /desktop:\s*1439/);

const images = readFeatureFile("ImagePolicy.ts");
assert.match(images, /ALLOWED_REMOTE_IMAGE_HOSTS/);
assert.match(images, /images\.unsplash\.com/);
assert.match(images, /url\.protocol === "https:"/);
assert.doesNotMatch(images, /url\.protocol === "http:"/);

const runtime = readFeatureFile("RuntimeChecks.ts");
assert.match(runtime, /toDataURL\("image\/webp"\)/);
assert.match(runtime, /prefers-reduced-motion/);

const conversion = readFeatureFile("ConversionEvents.ts");
assert.match(conversion, /EVENT_NAMES\.has\(event\.name\)/);
assert.match(conversion, /SAFE_MARKET_CODE/);
assert.match(conversion, /SAFE_ID/);
assert.match(conversion, /return null/);

const guards = readFeatureFile("ProductionGuards.ts");
assert.match(guards, /PUBLIC_APP_URL_NOT_HTTPS/);
assert.match(guards, /AUTH_SECRET_MISSING/);

const packagePath = path.join(root, "package.json");
const packageJson = JSON.parse(
  fs.readFileSync(packagePath, "utf8"),
);

assert.equal(
  packageJson.scripts["verify:f13"],
  "node ./scripts/verify-f13.mjs",
  "verify:f13 must point to the correctly named verifier",
);

assert.match(
  packageJson.scripts.verify,
  /npm run verify:f13/,
  "Main verify command must include F13 verification",
);

console.log(
  "F13 structural verification passed: " +
    requiredFiles.length +
    " feature files, privacy policy, responsive breakpoints, " +
    "image allowlist, runtime checks, conversion validation, " +
    "production guards and npm script wiring.",
);
