// Builds the panel into one ES module, the same bytes for the same sources and lock file (no timestamp, no
// source map, no absolute path): CI rebuilds it and fails when the committed file differs.
import { build } from "esbuild";

await build({
  entryPoints: ["src/weishaupt-panel.ts"],
  outfile: "../custom_components/weishaupt/frontend/dist/weishaupt-panel.js",
  bundle: true,
  format: "esm",
  target: "es2021",
  minify: true,
  legalComments: "eof",
  sourcemap: false,
  logLevel: "info",
});
