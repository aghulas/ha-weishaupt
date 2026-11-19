// Builds the panel and the dashboard card, one ES module each, the same bytes for the same sources and lock file (no timestamp, no
// source map, no absolute path): CI rebuilds it and fails when the committed file differs.
import { build } from "esbuild";

await build({
  entryPoints: { "weishaupt-panel": "src/weishaupt-panel.ts", "weishaupt-card": "src/weishaupt-card.ts" },
  outdir: "../custom_components/weishaupt/frontend/dist",
  bundle: true,
  format: "esm",
  target: "es2021",
  minify: true,
  legalComments: "eof",
  sourcemap: false,
  logLevel: "info",
});
