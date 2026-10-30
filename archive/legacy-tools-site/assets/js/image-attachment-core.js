(function (root) {
  "use strict";
  const limits = {
    bytes: 20000000,
    pixels: 24000000,
    edge: 8192,
    outputEdge: 4096,
  };
  function inspect(buffer) {
    const b = new Uint8Array(buffer);
    const v = new DataView(buffer);
    if (!b.length || b.length > limits.bytes)
      throw new Error(
        "Choose a non-empty image up to 20 MB (20,000,000 bytes).",
      );
    let width, height, type;
    if (
      b.length >= 33 &&
      [137, 80, 78, 71, 13, 10, 26, 10].every((n, i) => b[i] === n)
    ) {
      type = "image/png";
      let pos = 8,
        ended = false;
      while (pos + 12 <= b.length) {
        const size = v.getUint32(pos);
        if (pos + size + 12 > b.length)
          throw new Error("This PNG is incomplete. Choose another file.");
        const name = String.fromCharCode(...b.subarray(pos + 4, pos + 8));
        if (pos === 8) {
          if (name !== "IHDR" || size !== 13)
            throw new Error("This PNG header is invalid.");
          width = v.getUint32(pos + 8);
          height = v.getUint32(pos + 12);
        }
        if (name === "acTL")
          throw new Error(
            "Animated PNG is not supported. Choose a still JPG or PNG.",
          );
        pos += size + 12;
        if (name === "IEND") {
          ended = true;
          break;
        }
      }
      if (!ended)
        throw new Error("This PNG is incomplete. Choose another file.");
    } else if (b.length > 4 && b[0] === 255 && b[1] === 216 && b[2] === 255) {
      type = "image/jpeg";
      let pos = 2;
      while (pos + 4 <= b.length) {
        if (b[pos++] !== 255) throw new Error("This JPEG header is invalid.");
        while (b[pos] === 255) pos++;
        const marker = b[pos++];
        if (marker === 217 || marker === 218) break;
        if (marker === 1 || (marker >= 208 && marker <= 215)) continue;
        if (pos + 2 > b.length) break;
        const size = v.getUint16(pos);
        if (size < 2 || pos + size > b.length)
          throw new Error("This JPEG is incomplete. Choose another file.");
        if (
          [
            192, 193, 194, 195, 197, 198, 199, 201, 202, 203, 205, 206, 207,
          ].includes(marker)
        ) {
          if (size < 8) throw new Error("This JPEG header is invalid.");
          height = v.getUint16(pos + 3);
          width = v.getUint16(pos + 5);
        }
        pos += size;
      }
    } else
      throw new Error(
        "Choose a still JPG or PNG. HEIC, GIF, WebP and other formats are not supported as input.",
      );
    if (!width || !height)
      throw new Error(
        "The image dimensions could not be read. Choose another file.",
      );
    if (
      width > limits.edge ||
      height > limits.edge ||
      width * height > limits.pixels
    )
      throw new Error(
        "Choose an image up to 24 megapixels, with each side at most 8192 px.",
      );
    return { width, height, type };
  }
  function fit(width, height, maxWidth, maxHeight) {
    const scale = Math.min(1, maxWidth / width, maxHeight / height);
    return {
      width: Math.max(1, Math.floor(width * scale)),
      height: Math.max(1, Math.floor(height * scale)),
    };
  }
  function number(value, label, max, fallback) {
    if (value.trim() === "") return fallback;
    const n = Number(value);
    if (!Number.isInteger(n) || n < 1 || n > max)
      throw new Error(
        label + " must be a whole number from 1 to " + max + ", or left blank.",
      );
    return n;
  }
  function options(values) {
    if (!["image/jpeg", "image/png"].includes(values.type))
      throw new Error("Choose JPG or PNG output.");
    const quality = Number(values.quality);
    if (![0.75, 0.5, 0.3].includes(quality))
      throw new Error("Choose a minimum JPG quality.");
    return {
      type: values.type,
      quality,
      shrink: Boolean(values.shrink),
      target:
        number(values.size, "Maximum file size (KB)", 20000, Infinity) * 1000,
      maxWidth: number(
        values.width,
        "Maximum width",
        limits.outputEdge,
        limits.outputEdge,
      ),
      maxHeight: number(
        values.height,
        "Maximum height",
        limits.outputEdge,
        limits.outputEdge,
      ),
    };
  }
  const api = { limits, inspect, fit, options };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ImageAttachmentCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
