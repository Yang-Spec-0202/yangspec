const { test } = require("node:test");
const assert = require("node:assert/strict");
const data = require("../data/planner.json");
const { estimate, storage } = require("../assets/js/planner-model.js");
const base = {
  apps: ["vaultwarden"],
  users: 1,
  storageTb: 0,
  playback: "direct",
  ml: true,
};
const plan = (overrides) => estimate(data, { ...base, ...overrides });

test("empty choices produce no recommendation or invented price", () => {
  const result = plan({ apps: [] });
  assert.equal(result.status, "empty");
  assert.equal(result.subtotal, undefined);
});
test("a light service has a small target but unquoted costs remain unknown", () => {
  const result = plan();
  assert.equal(result.ramGb, 2);
  assert.equal(result.cpu, 1);
  assert.equal(result.subtotal, null);
  assert.equal(result.complete, false);
  assert.equal(result.unknown.length, 6);
});
test("Immich respects official system guidance and its ML-disabled exception", () => {
  const on = plan({ apps: ["immich"] });
  const off = plan({ apps: ["immich"], ml: false });
  assert.ok(on.ramGb >= 8);
  assert.ok(on.cpu >= 4);
  assert.ok(off.ramGb >= 4);
  assert.ok(off.ramGb < on.ramGb);
});
test("PhotoPrism and Jellyfin cannot be sized below retrieved hardware guidance", () => {
  const photo = plan({ apps: ["photoprism"] });
  assert.ok(photo.ramGb >= 3);
  assert.ok(photo.cpu >= 2);
  assert.ok(plan({ apps: ["jellyfin"] }).ramGb >= 8);
});
test("2 TB of media affects primary capacity, separate backup and storage cost", () => {
  const quotes = {
    server: 20,
    includedGb: 100,
    storageRate: 0.02,
    backupRate: 0.01,
    network: 0,
    extras: 1,
    management: 0,
  };
  const result = plan({
    apps: ["jellyfin", "immich"],
    storageTb: 2,
    playback: "hardware",
    quotes,
  });
  assert.equal(result.primaryGb, 3024);
  assert.equal(result.backupGb, 2520);
  assert.equal(result.needsHardware, true);
  assert.ok(Math.abs(result.subtotal - 104.68) < 1e-8);
  assert.equal(result.complete, true);
  const small = plan({ apps: ["jellyfin", "immich"], storageTb: 0, quotes });
  assert.ok(result.subtotal > small.subtotal);
});
test("software transcode is explicitly unsized; GPU mode never claims compatibility", () => {
  assert.equal(
    plan({ apps: ["jellyfin"], playback: "software" }).softwareUnspecified,
    true,
  );
  assert.equal(
    plan({ apps: ["vaultwarden"], playback: "hardware" }).needsHardware,
    false,
  );
});
test("a full mixed stack with many users is not clamped to an insufficient tier", () => {
  const result = plan({ apps: data.apps.map((app) => app.id), users: 20 });
  assert.ok(result.ramGb > 32 || result.cpu > 8);
  assert.equal(result.oversized, true);
});
test("negative, non-finite, missing and out-of-range workload inputs are rejected", () => {
  for (const value of [-1, NaN, Infinity, "not a number", "", 101])
    assert.equal(plan({ storageTb: value }).status, "invalid");
  for (const value of [0, -1, 1.5, 21, Infinity, ""])
    assert.equal(plan({ users: value }).status, "invalid");
  assert.equal(plan({ quotes: { storageRate: -0.1 } }).status, "invalid");
});
test("unknown quotes differ from confirmed zero; included capacity costs no extra", () => {
  const result = plan({
    quotes: {
      server: 5,
      includedGb: 100,
      backupRate: 0,
      network: 0,
      extras: 0,
      management: 0,
    },
  });
  assert.equal(result.complete, true);
  assert.equal(result.subtotal, 5);
  assert.equal(plan({ quotes: { server: 5 } }).complete, false);
});
test("more users or library capacity never decreases the capacity target", () => {
  for (const app of data.apps) {
    const one = plan({ apps: [app.id] });
    const many = plan({ apps: [app.id], users: 20, storageTb: 3 });
    assert.ok(many.ramGb >= one.ramGb);
    assert.ok(many.cpu >= one.cpu);
    assert.ok(many.primaryGb > one.primaryGb);
  }
});
test("catalog identifiers, presets and references are consistent", () => {
  assert.equal(new Set(data.apps.map((app) => app.id)).size, data.apps.length);
  for (const app of data.apps) {
    assert.ok(data.groups.some((group) => group.id === app.group));
    assert.ok(new URL(app.source).protocol === "https:");
    assert.ok(app.context);
  }
  for (const preset of data.presets)
    for (const id of preset.apps)
      assert.ok(data.apps.some((app) => app.id === id));
  assert.equal(storage(1000), "1 TB");
  assert.equal(storage(3024), "3.02 TB");
});
