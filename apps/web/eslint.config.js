import tseslint from "typescript-eslint";
export default tseslint.config(
  { ignores: ["src/api/schema.d.ts", "dist/**"] },
  ...tseslint.configs.recommended,
);
