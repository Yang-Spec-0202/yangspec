(function () {
  "use strict";
  const root = document.querySelector("#attachment-helper");
  if (!root) return;
  const core = window.ImageAttachmentCore;
  const $ = (id) => document.getElementById(id);
  const form = $("attachment-form"),
    fileInput = $("attachment-file"),
    sampleButton = $("attachment-sample");
  const status = $("attachment-status"),
    error = $("attachment-error");
  const canvas = document.createElement("canvas");
  const supported =
    !!core &&
    typeof createImageBitmap === "function" &&
    typeof canvas.toBlob === "function";
  let source = null,
    originalURL = null,
    resultURL = null,
    job = 0,
    busy = false;
  const bytes = (n) =>
    n.toLocaleString("en-US") + " bytes (" + (n / 1000).toFixed(2) + " KB)";
  function message(text) {
    status.textContent = text;
  }
  function clearResult() {
    if (resultURL) URL.revokeObjectURL(resultURL);
    resultURL = null;
    $("attachment-result").hidden = true;
    $("attachment-after").removeAttribute("src");
    $("attachment-download").removeAttribute("href");
  }
  function controls(working) {
    busy = working;
    $("attachment-prepare").disabled = working || !source;
    $("attachment-cancel").hidden = !working;
    $("attachment-options").disabled = working;
    sampleButton.disabled = working || !supported;
    root.setAttribute("aria-busy", String(working));
  }
  function stop() {
    job++;
    controls(false);
    canvas.width = canvas.height = 1;
  }
  function releaseSource() {
    if (source) source.bitmap.close();
    source = null;
    if (originalURL) URL.revokeObjectURL(originalURL);
    originalURL = null;
    $("attachment-source").hidden = true;
    $("attachment-before").removeAttribute("src");
    $("attachment-source-details").textContent = "";
  }
  function fail(e) {
    error.textContent = e.message;
    error.hidden = false;
    error.focus();
    message("No new attachment was created.");
  }
  function hideError() {
    error.hidden = true;
    error.textContent = "";
  }
  async function loadFile(file) {
    stop();
    clearResult();
    releaseSource();
    hideError();
    controls(false);
    const current = job;
    if (!file) {
      message("Choose a JPG or PNG to begin.");
      return;
    }
    try {
      if (file.size > core.limits.bytes || file.size === 0)
        throw new Error(
          "Choose a non-empty image up to 20 MB (20,000,000 bytes).",
        );
      message("Reading the image on this device…");
      controls(true);
      const buffer = await file.arrayBuffer();
      if (current !== job) return;
      const header = core.inspect(buffer);
      let bitmap;
      try {
        bitmap = await createImageBitmap(
          new Blob([buffer], { type: header.type }),
          { imageOrientation: "from-image" },
        );
      } catch {
        throw new Error(
          "This browser could not decode the image. It may be damaged, or this device may be short of memory. Try a smaller JPG or PNG.",
        );
      }
      if (current !== job) {
        bitmap.close();
        return;
      }
      if (
        bitmap.width * bitmap.height > core.limits.pixels ||
        bitmap.width > core.limits.edge ||
        bitmap.height > core.limits.edge
      ) {
        bitmap.close();
        throw new Error("The decoded image exceeds the supported dimensions.");
      }
      originalURL = URL.createObjectURL(
        new Blob([buffer], { type: header.type }),
      );
      source = { bitmap, size: file.size, type: header.type };
      $("attachment-before").src = originalURL;
      $("attachment-source-details").textContent =
        bytes(file.size) +
        " · " +
        bitmap.width +
        " × " +
        bitmap.height +
        " px · " +
        (header.type === "image/jpeg" ? "JPG" : "PNG");
      $("attachment-source").hidden = false;
      controls(false);
      message(
        "Image ready. Enter the requirements you checked, then prepare the attachment.",
      );
    } catch (e) {
      if (current === job) {
        controls(false);
        fail(e);
      }
    }
  }
  function encode(type, quality, current) {
    return new Promise((resolve, reject) => {
      canvas.toBlob(
        (blob) => {
          if (current !== job) {
            reject(new Error("cancelled"));
            return;
          }
          if (!blob || !blob.size) {
            reject(
              new Error(
                "This device could not create the attachment. Try smaller dimensions or a smaller source image.",
              ),
            );
            return;
          }
          if (blob.type !== type) {
            reject(
              new Error(
                "Your browser cannot encode the selected format. Choose another output format.",
              ),
            );
            return;
          }
          resolve(blob);
        },
        type,
        quality,
      );
    });
  }
  async function atSize(size, settings, current) {
    canvas.width = size.width;
    canvas.height = size.height;
    const ctx = canvas.getContext("2d");
    if (!ctx)
      throw new Error("Image processing is unavailable on this device.");
    if (settings.type === "image/jpeg") {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, size.width, size.height);
    }
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(source.bitmap, 0, 0, size.width, size.height);
    let best = await encode(settings.type, 0.92, current);
    let quality = settings.type === "image/png" ? null : 0.92;
    if (best.size <= settings.target || quality === null)
      return { blob: best, quality, ...size };
    const lowBlob = await encode(settings.type, settings.quality, current);
    if (lowBlob.size > settings.target)
      return { blob: lowBlob, quality: settings.quality, ...size };
    best = lowBlob;
    quality = settings.quality;
    let low = quality,
      high = 0.92;
    for (let i = 0; i < 7; i++) {
      const mid = (low + high) / 2;
      const blob = await encode(settings.type, mid, current);
      if (blob.size <= settings.target) {
        best = blob;
        quality = mid;
        low = mid;
      } else high = mid;
    }
    return { blob: best, quality, ...size };
  }
  async function prepare(event) {
    event.preventDefault();
    if (!source || busy) return;
    clearResult();
    hideError();
    let settings;
    try {
      for (const id of [
        "attachment-size",
        "attachment-width",
        "attachment-height",
      ]) {
        if ($(id).validity.badInput)
          throw new Error(
            "Enter a valid whole number, or leave the field blank.",
          );
      }
      settings = core.options({
        type: $("attachment-format").value,
        size: $("attachment-size").value,
        width: $("attachment-width").value,
        height: $("attachment-height").value,
        quality: $("attachment-quality").value,
        shrink: $("attachment-shrink").checked,
      });
    } catch (e) {
      fail(e);
      return;
    }
    const current = ++job;
    controls(true);
    message("Preparing on this device. You can cancel or clear the image.");
    try {
      let size = core.fit(
        source.bitmap.width,
        source.bitmap.height,
        settings.maxWidth,
        settings.maxHeight,
      );
      let output = await atSize(size, settings, current);
      for (
        let i = 0;
        settings.shrink &&
        output.blob.size > settings.target &&
        i < 8 &&
        Math.max(size.width, size.height) > 64;
        i++
      ) {
        if (current !== job) return;
        const scale = Math.max(0.8, 64 / Math.max(size.width, size.height));
        size = {
          width: Math.max(1, Math.floor(size.width * scale)),
          height: Math.max(1, Math.floor(size.height * scale)),
        };
        message(
          "Trying " +
            size.width +
            " × " +
            size.height +
            " px. Review fine text before using the result.",
        );
        output = await atSize(size, settings, current);
      }
      if (current !== job) return;
      // Decode the encoded result before offering it for download.
      let check;
      try {
        check = await createImageBitmap(output.blob);
      } catch {
        throw new Error(
          "The output could not be verified. Try a smaller image or another format.",
        );
      }
      const valid =
        check.width === output.width && check.height === output.height;
      check.close();
      if (current !== job) return;
      if (!valid)
        throw new Error(
          "The output dimensions could not be verified. Please try again.",
        );
      resultURL = URL.createObjectURL(output.blob);
      $("attachment-after").src = resultURL;
      const met = output.blob.size <= settings.target;
      const format = settings.type === "image/jpeg" ? "JPG" : "PNG";
      $("attachment-result-details").textContent =
        bytes(output.blob.size) +
        " · " +
        output.width +
        " × " +
        output.height +
        " px · " +
        format;
      $("attachment-outcome").textContent =
        settings.target === Infinity
          ? "Ready for your review"
          : met
            ? "Within your file size limit"
            : "Above your file size limit";
      $("attachment-outcome").classList.toggle("attachment-warning", !met);
      $("attachment-result-note").textContent =
        (!met
          ? "This file does not meet your size limit. Increase the limit, allow smaller dimensions, choose JPG, or lower the minimum JPG quality. "
          : "") +
        (settings.type === "image/jpeg"
          ? "JPG changes image detail and replaces transparency with white. "
          : "PNG keeps transparency; resizing still changes detail. ") +
        "Compare at full size, especially text. The receiving service decides whether to accept the file.";
      $("attachment-quality-note").textContent =
        output.quality === null
          ? "PNG encoding has no JPG quality setting."
          : "JPG encoder quality: " +
            Math.round(output.quality * 100) +
            "/100. This is an encoder setting, not a measured visual quality score.";
      const link = $("attachment-download");
      link.href = resultURL;
      link.download =
        "yangspec-attachment." + (format === "JPG" ? "jpg" : "png");
      link.textContent = met
        ? "Download " + format
        : "Download " + format + " above limit";
      $("attachment-result").hidden = false;
      controls(false);
      canvas.width = canvas.height = 1;
      message(
        met
          ? "Attachment ready. Review the preview and download it."
          : "Attachment created, but your size limit was not met.",
      );
      $("attachment-result").focus();
    } catch (e) {
      if (current === job) {
        controls(false);
        canvas.width = canvas.height = 1;
        fail(e);
      }
    }
  }
  fileInput.addEventListener("change", () => loadFile(fileInput.files[0]));
  sampleButton.addEventListener("click", async () => {
    stop();
    clearResult();
    releaseSource();
    hideError();
    fileInput.value = "";
    const current = job;
    controls(true);
    message("Loading the public example from this site…");
    try {
      const response = await fetch(sampleButton.dataset.sampleUrl);
      if (!response.ok) throw new Error("sample unavailable");
      const sample = await response.blob();
      if (current === job) await loadFile(sample);
    } catch {
      if (current === job) {
        controls(false);
        fail(
          new Error(
            "The public example could not be loaded. Try again, or choose a JPG or PNG from your device.",
          ),
        );
      }
    }
  });
  form.addEventListener("submit", prepare);
  $("attachment-options").addEventListener("input", () => {
    clearResult();
    hideError();
    if (source)
      message("Settings changed. Prepare a new attachment to apply them.");
  });
  $("attachment-format").addEventListener("change", () => {
    $("attachment-quality").disabled =
      $("attachment-format").value === "image/png";
  });
  $("attachment-cancel").addEventListener("click", () => {
    stop();
    clearResult();
    if (!source) fileInput.value = "";
    message(
      source
        ? "Cancelled. Change the settings and try again."
        : "Cancelled. Choose the image again.",
    );
    (source ? $("attachment-prepare") : fileInput).focus();
  });
  $("attachment-clear").addEventListener("click", () => {
    stop();
    clearResult();
    releaseSource();
    form.reset();
    hideError();
    controls(false);
    $("attachment-quality").disabled = false;
    message(
      "Image and result cleared from this page. Choose another image to begin.",
    );
    fileInput.focus();
  });
  $("attachment-download").addEventListener("click", () => {
    message(
      "Download requested. Check your browser’s downloads or save menu; this page cannot confirm that the file was saved.",
    );
  });
  window.addEventListener("pagehide", () => {
    stop();
    clearResult();
    releaseSource();
    controls(false);
    fileInput.value = "";
    message("Choose a JPG or PNG to begin.");
  });
  if (!supported) {
    fileInput.disabled = true;
    sampleButton.disabled = true;
    fail(
      new Error(
        "This browser lacks the image features needed here. Try a current browser with Canvas and createImageBitmap support.",
      ),
    );
  }
})();
