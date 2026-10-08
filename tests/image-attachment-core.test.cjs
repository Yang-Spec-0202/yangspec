const { test } = require("node:test");
const assert = require("node:assert/strict");
const {
  inspect,
  fit,
  options,
} = require("../assets/js/image-attachment-core.js");
function png(w, h, animated = false) {
  const chunks = [
    ["IHDR", 13],
    ...(animated ? [["acTL", 8]] : []),
    ["IEND", 0],
  ];
  const b = Buffer.alloc(8 + chunks.reduce((n, [, len]) => n + len + 12, 0));
  Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]).copy(b);
  let pos = 8;
  for (const [name, len] of chunks) {
    b.writeUInt32BE(len, pos);
    b.write(name, pos + 4);
    if (name === "IHDR") {
      b.writeUInt32BE(w, pos + 8);
      b.writeUInt32BE(h, pos + 12);
    }
    pos += len + 12;
  }
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.length);
}
test("Preflight rejects resource excess before a decoder allocates pixels", () => {
  assert.deepEqual(inspect(png(6000, 4000)), {
    width: 6000,
    height: 4000,
    type: "image/png",
  });
  assert.throws(() => inspect(png(6000, 4001)), /24 megapixels/);
  assert.throws(() => inspect(png(8193, 1)), /8192/);
  assert.throws(() => inspect(new ArrayBuffer(20000001)), /20 MB/);
});
test("Reject animated, truncated and unsupported inputs", () => {
  assert.throws(() => inspect(png(30, 20, true)), /Animated/);
  assert.throws(() => inspect(png(30, 20).slice(0, -1)), /incomplete/);
  assert.throws(() => inspect(new ArrayBuffer(0)), /non-empty/);
  assert.throws(
    () => inspect(Uint8Array.from([71, 73, 70, 56, 57, 97]).buffer),
    /still JPG or PNG/,
  );
});
test("Fit keeps proportions, bounds, tiny dimensions and avoids enlargement", () => {
  assert.deepEqual(fit(4000, 3000, 1600, 1600), { width: 1600, height: 1200 });
  assert.deepEqual(fit(40, 30, 100, 100), { width: 40, height: 30 });
  assert.deepEqual(fit(1, 8192, 4096, 1), { width: 1, height: 1 });
});
test("Blank limits differ from zero; KB is decimal and invalid targets reject", () => {
  const base = {
    type: "image/jpeg",
    quality: "0.5",
    size: "",
    width: "",
    height: "",
    shrink: false,
  };
  assert.equal(options(base).target, Infinity);
  assert.equal(options({ ...base, size: "200" }).target, 200000);
  for (const size of ["0", "-1", "1.5", "NaN", "20001"])
    assert.throws(() => options({ ...base, size }));
  assert.throws(() => options({ ...base, width: "4097" }));
  assert.throws(() => options({ ...base, type: "image/webp" }));
});
