import js from "@eslint/js";
import boundaries from "eslint-plugin-boundaries";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

// Mirrors the backend's import-linter layer contract
// (docs/project-structure.md §5): shared -> features -> portals -> app.
// features may only reach each other through index.ts, the same
// services.py/selectors.py discipline used on the backend
// (docs/frontend-architecture.md §5).
export default tseslint.config(
  { ignores: ["dist", "src/shared/lib/api-types.ts"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      globals: { window: "readonly", document: "readonly" },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      boundaries,
    },
    settings: {
      "boundaries/elements": [
        { type: "shared", pattern: "src/shared/**" },
        { type: "features", pattern: "src/features/*/**", capture: ["feature"] },
        { type: "portals", pattern: "src/portals/*/**", capture: ["portal"] },
        { type: "app", pattern: "src/app/**" },
      ],
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      "boundaries/element-types": [
        "error",
        {
          default: "disallow",
          rules: [
            { from: "shared", allow: ["shared"] },
            { from: "features", allow: ["shared", "features"] },
            { from: "portals", allow: ["shared", "features", "portals"] },
            { from: "app", allow: ["shared", "features", "portals", "app"] },
          ],
        },
      ],
      "boundaries/entry-point": [
        "error",
        {
          default: "disallow",
          rules: [{ target: "features", allow: "index.ts" }],
        },
      ],
    },
  },
);
