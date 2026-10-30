---
title: "Image Attachment Helper: Resize and Compress JPG or PNG"
date: 2026-10-06
lastmod: 2026-10-08
description: "Prepare a JPG or PNG for an email or upload form. Set your maximum file size and dimensions, compare the result, then download."
layout: "image-attachment"
imageAttachment: true
ShowToc: false
draft: false
---

{{< image-attachment-helper >}}

## Before you attach it

You can **try a public example** without choosing a personal file. The sample is a 1200 × 800 px PNG with large and fine text, loaded from this site. Try a maximum width of **600 px**, then review which details remain readable. These are example settings, not the requirements of your form.

Check the receiving service’s requirements yourself. This tool uses maximum dimensions, keeps the whole image and preserves its proportions. It cannot make an exact passport crop or guarantee acceptance by an institution. For example, set **200 KB**, **1600 px** width and **1600 px** height for requirements you have confirmed; a landscape image will keep its landscape shape.

JPG usually suits photographs. It uses lossy compression and replaces transparent areas with white. PNG keeps transparent areas and can suit screenshots, but a strict size limit may require smaller dimensions. Leave the optional resize checkbox off when you need to keep the dimensions you entered. Preview text, faces and fine lines at full size before using the attachment. You can open the preview in a new tab using your browser’s image menu.

## Support and limits

- One static JPG or PNG at a time: up to **20 MB (20,000,000 bytes)**, **24 megapixels** and **8192 px per side**. The output is capped at **4096 px per side**. These are tool limits; a device with little memory may fail on smaller images.
- JPG/PNG output depends on your browser’s actual encoder. An unsupported format or an output that cannot be decoded produces an error, with no download offered.
- Photo orientation follows the image’s EXIF orientation when decoded by a compatible browser. Canvas re-encoding changes metadata; do not use this tool when you need original EXIF, colour profiles, print DPI, archival fidelity or exact colour matching.
- HEIC, GIF, animated PNG, WebP input, multiple files, SVG, PDFs and damaged files are outside this version’s scope. Convert to a still JPG/PNG using a trusted application first.
- A very small size limit may be impossible at your chosen quality and dimensions. The result shows the actual bytes and clearly marks files above the limit. Encoder quality is a setting, not a measured quality score.

## Files and privacy

Processing uses your browser’s image decoder and Canvas encoder. File contents, names and your requirements are not uploaded, added to links, stored in page storage or sent to analytics by this tool. The browser may cache temporary image data according to its own behavior. **Clear image & settings** releases the tool’s image references; leaving the page also releases them. Neither action removes files you have downloaded.

The public example makes a normal request for this site’s sample PNG. Your own files do not use that request path.

The site uses Cloudflare page visit and performance analytics on production, under the existing regional configuration. Those page statistics are separate from image processing; this tool adds no download or completion tracking. See [Privacy](/privacy/) for the site’s current policy.

Technical references: [Canvas image encoding](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob) and [browser image decoding and orientation](https://developer.mozilla.org/en-US/docs/Web/API/Window/createImageBitmap), reviewed October 6, 2026.
