module.exports = {
  root: true,
  env: { browser: true, node: true },
  parser: "@typescript-eslint/parser",
  plugins: ["@typescript-eslint", "import"],
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended", "prettier"],
  ignorePatterns: ["node_modules", "dist", "build", ".expo", "android", "ios"],
  rules: {
    "import/order": ["warn", { "newlines-between": "always" }]
  }
};
