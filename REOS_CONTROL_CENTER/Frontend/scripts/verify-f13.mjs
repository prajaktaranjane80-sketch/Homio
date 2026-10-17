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
  "PolicyImage.tsx",
  "ErrorBoundary.tsx",
  "LoadingBoundary.tsx",
  "ProductionQualityMonitor.tsx",
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

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

function readFeature(name) {
  return read(path.join("src", "features", "f13_production", name));
}

const analytics = readFeature("AnalyticsEvents.ts");
assert.match(analytics, /SAFE_PROPERTY_KEYS/);
assert.match(analytics, /SAFE_PROPERTY_KEYS\.has\(key\)/);
assert.match(analytics, /Analytics must never interrupt/i);
assert.doesNotMatch(
  analytics,
  /FORBIDDEN_PROPERTY_KEYS\.has\(normalizedKey\)/,
);

const responsive = readFeature("ResponsiveAudit.tsx");
assert.match(responsive, /mobile:\s*767/);
assert.match(responsive, /tablet:\s*1023/);
assert.match(responsive, /desktop:\s*1439/);

const images = readFeature("ImagePolicy.ts");
assert.match(images, /ALLOWED_REMOTE_IMAGE_HOSTS/);
assert.match(images, /images\.unsplash\.com/);
assert.match(images, /url\.protocol === "https:"/);
assert.doesNotMatch(images, /url\.protocol === "http:"/);

const policyImage = readFeature("PolicyImage.tsx");
assert.match(policyImage, /isAllowedImageSource\(src\)/);
assert.match(policyImage, /getImageQuality/);
assert.match(policyImage, /getImagePolicy/);

const runtime = readFeature("RuntimeChecks.ts");
assert.match(runtime, /toDataURL\("image\/webp"\)/);
assert.match(runtime, /prefers-reduced-motion/);

const monitor = readFeature("ProductionQualityMonitor.tsx");
assert.match(monitor, /auditAccessibility/);
assert.match(monitor, /auditResponsiveDimensions/);
assert.match(monitor, /runRuntimeChecks/);

const conversion = readFeature("ConversionEvents.ts");
assert.match(conversion, /EVENT_NAMES\.has\(event\.name\)/);
assert.match(conversion, /SAFE_MARKET_CODE/);
assert.match(conversion, /SAFE_ID/);
assert.match(conversion, /return null/);

const guards = readFeature("ProductionGuards.ts");
assert.match(guards, /PUBLIC_APP_URL_NOT_HTTPS/);
assert.match(guards, /AUTH_SECRET_MISSING/);
assert.match(guards, /AUTH_PROVIDER_CONFIGURATION_MISSING/);

const layout = read("src/app/layout.tsx");
assert.match(layout, /features\/f13_production\/ErrorBoundary/);
assert.match(layout, /ProductionQualityMonitor/);
assert.match(layout, /<ErrorBoundary>/);

const loading = read("src/app/loading.tsx");
assert.match(loading, /features\/f13_production\/LoadingBoundary/);

assert.match(read("src/app/page.tsx"), /createSeoMetadata/);
assert.match(read("src/app/search/page.tsx"), /createSeoMetadata/);

const featuredProjects = read("src/features/f02_home_discovery/FeaturedProjects.tsx");
assert.match(featuredProjects, /features\/f13_production\/PolicyImage/);
assert.doesNotMatch(featuredProjects, /import Image from "next\/image"/);

const nextConfig = read("next.config.ts");
assert.match(nextConfig, /qualities:\s*\[60,\s*75,\s*85\]/);

assert.match(
  read("src/features/f06_save_compare/CompareEmptyState.tsx"),
  /getEmptyStateCopy\("no-comparisons"\)/,
);

const instrumentation = read("src/instrumentation.ts");
assert.match(instrumentation, /inspectProductionConfiguration/);
assert.match(instrumentation, /HOMIO_SESSION_SECRET/);
assert.match(instrumentation, /HOMIO_OIDC_ISSUER/);

const packageJson = JSON.parse(read("package.json"));
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
  "F13 integration verification passed: " +
    requiredFiles.length +
    " feature files, shared route boundaries, SEO metadata, image policy, " +
    "empty-state policy, runtime diagnostics and production guard wiring.",
);
