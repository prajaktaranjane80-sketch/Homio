import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      "node_modules/**",
      "dist/**",
      "coverage/**"
    ]
  },

  eslint.configs.recommended,

  ...tseslint.configs.recommended,

  {
    files: [
      "src/**/*.ts",
      "tests/**/*.ts",
      "vitest.config.ts"
    ],

    rules: {
      "no-undef": "off",

      "@typescript-eslint/consistent-type-imports": [
        "error",
        {
          "prefer": "type-imports"
        }
      ],

      "@typescript-eslint/no-explicit-any": "error",

      "@typescript-eslint/no-non-null-assertion": "error"
    }
  }
);
