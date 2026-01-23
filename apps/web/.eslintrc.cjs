module.exports = {
  root: true,
  extends: ["next/core-web-vitals", "prettier"],
  rules: {
    "import/order": ["warn", { "newlines-between": "always" }]
  }
};
