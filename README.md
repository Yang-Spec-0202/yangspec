# YangSpec

A Hugo / PaperMod site with a browser-local self-hosting planner. Production uses Cloudflare Pages; a push to `main` deploys the live site. Use a branch and a Pages preview to review changes.

## Local development

Use Hugo Extended 0.167.0 or the production build's pinned version, then run `hugo server`. PaperMod is checked into `themes/PaperMod` as ordinary tracked files; there is no theme submodule to initialize. The site needs no frontend package installation.

Run `node --test tests/planner-model.test.cjs` (Node 22+), `node --check assets/js/planner.js`, and `hugo --environment production` before deploying. The inherited PaperMod `.Language.LanguageCode` deprecation warning does not prevent the current build; review theme compatibility before upgrading Hugo.

## Planner maintenance

- `data/planner.json` is the shared catalog for the homepage examples and planner. Each app has a deployment/reference source and an explicit planning allowance. These are not benchmark results. Recheck official system guidance before changing documented floors, and update the review date.
- `assets/js/planner-model.js` contains the calculation only; Node tests cover unknown versus zero prices, storage and backup costs, official floors, invalid inputs, playback limits and workloads above the starter range.
- `assets/js/planner.js` renders accessible controls/results. Quote values stay in memory on this page, are not persisted or sent to a server, and only go to the clipboard after an explicit copy action.
- `assets/css/extended/yangspec.css` controls the shared design; `assets/css/planner.css` loads on tools pages. Hugo fingerprints and minifies shipped CSS/JS. Keep the source readable.
- `layouts/` overrides theme templates. Preserve current article URLs when updating content and keep formula explanations consistent with the model.

## Review before release

Check home, planner (empty and selected states), and a guide at 320, 390, 768, 1024 and 1440 px, in both themes. Cover keyboard navigation, visible focus, errors, result/edit navigation, copying, reset and reduced motion. Run Lighthouse on the Pages preview; repeated lab scores do not establish real-user Core Web Vitals or full accessibility conformance.

Avoid unverified provider rankings, generic prices that exclude required storage, or claims that a VPS supports hardware transcoding without confirmed device access. Keep secrets and authentication material out of source and reports.
