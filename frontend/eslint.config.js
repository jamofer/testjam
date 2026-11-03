import js from "@eslint/js"
import react from "eslint-plugin-react"
import reactHooks from "eslint-plugin-react-hooks"
import globals from "globals"

export default [
  { ignores: ["dist/", "node_modules/", "coverage/"] },
  js.configs.recommended,
  react.configs.flat.recommended,
  react.configs.flat["jsx-runtime"],
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: { ...globals.browser },
    },
    settings: { react: { version: "detect" } },
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // Props are documented by usage; the codebase does not use PropTypes.
      "react/prop-types": "off",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_", caughtErrors: "none" }],
    },
  },
  {
    files: ["src/__tests__/**", "**/*.test.{js,jsx}"],
    languageOptions: { globals: { ...globals.node, ...globals.vitest } },
  },
  {
    files: ["*.config.js", "scripts/**"],
    languageOptions: { globals: { ...globals.node } },
  },
]
