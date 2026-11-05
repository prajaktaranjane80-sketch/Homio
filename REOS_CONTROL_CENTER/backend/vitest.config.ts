import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",

    include: [
      "tests/**/*.test.ts"
    ],

    exclude: [
      "node_modules",
      "dist",
      "coverage"
    ],

    clearMocks: true,
    restoreMocks: true,

    testTimeout: 10000,
    hookTimeout: 10000,

    sequence: {
      concurrent: false
    }
  }
});
