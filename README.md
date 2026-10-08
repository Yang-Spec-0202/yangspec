# YangSpec

## Current work

The planning workspace `E:\Projects\money\STATE.json` is the current status index. Read `AGENTS.md`, then the task card in the roadmap named by STATE. The former optimization plan and PR #2 are paused. G02/G03 add a browser-local image attachment helper, a homepage/toolbox entry and updated About/Privacy on their own branch from production. Do not merge the old candidate as part of this change. Preview and production identities are recorded separately in STATE.

The new helper accepts a single static JPG/PNG, checks input resource limits before decoding, and validates encoded output before download. Its independent files are `assets/js/image-attachment-core.js`, `assets/js/image-attachment.js`, `assets/css/image-attachment.css` and `content/tools/image-attachment-helper.md`. Run `node --test tests/image-attachment-core.test.cjs` alongside the existing planner regression; real-browser output/download checks are recorded in the planning G02 report.

A Hugo / PaperMod site with practical browser tools and self-hosting guides. Production uses Cloudflare Pages; a push to `main` deploys the live site. Use a branch and a Pages preview to review changes. The image tool can load a clearly labelled public sample from `static/samples/attachment-sample.png`; chosen user files never use that request path.

## Local development

Use Hugo Extended 0.167.0 or the production build's pinned version, then run `hugo server`. PaperMod is checked into `themes/PaperMod` as ordinary tracked files; there is no theme submodule to initialize. The site needs no frontend package installation.

Run `node --test tests/planner-model.test.cjs` (Node 22+), `node --check assets/js/planner.js`, and `hugo --environment production` before deploying. The inherited PaperMod `.Language.LanguageCode` deprecation warning does not prevent the current build; review theme compatibility before upgrading Hugo.

## Planner maintenance

- `data/planner.json` is the catalog for the planner. Each app has a deployment/reference source and an explicit planning allowance. These are not benchmark results. Recheck official system guidance before changing documented floors, and update the review date.
- `assets/js/planner-model.js` contains the calculation only; Node tests cover unknown versus zero prices, storage and backup costs, official floors, invalid inputs, playback limits and workloads above the starter range. The storage explanation uses the same returned components; their sum includes rounding and reconciles with primary capacity.
- `assets/js/planner.js` renders accessible controls/results. Quote values stay in memory on this page, are not persisted or sent to a server, and only go to the clipboard after an explicit copy action.
- `assets/css/extended/yangspec.css` controls the shared design; `assets/css/planner.css` loads on tools pages. Hugo fingerprints and minifies shipped CSS/JS. Keep the source readable.
- `layouts/` overrides theme templates. Preserve current article URLs when updating content and keep formula explanations consistent with the model.
- `static/favicon.svg` is the vector source for the brand icon. Keep the PNG, ICO and Safari mask derivatives synchronized with its mark and the header. Runtime pages need no image-processing dependency.

## Review before release

Check home, planner (empty and selected states), and a guide at 320, 390, 768, 1024 and 1440 px, in both themes. Cover keyboard navigation, visible focus, errors, result/edit navigation, copying, reset and reduced motion. Run Lighthouse on the Pages preview; repeated lab scores do not establish real-user Core Web Vitals or full accessibility conformance.

In the planner, type a value in the last quote field and press Tab. Focus must stay on “Why this size?”; Enter should open and close the explanation, and the next Tab should reach Copy plan. An unchanged blur event must not rebuild the focused result. Also verify select/checkbox changes, presets and reset still refresh the plan.

Avoid unverified provider rankings, generic prices that exclude required storage, or claims that a VPS supports hardware transcoding without confirmed device access. Keep secrets and authentication material out of source and reports.
