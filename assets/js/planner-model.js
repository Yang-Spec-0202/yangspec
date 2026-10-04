(function (root, factory) {
  const model = factory();
  if (typeof module === "object" && module.exports) module.exports = model;
  else root.YangSpecPlanner = model;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  function numeric(value, min, max, optional = false) {
    if (value === "" || value == null) return optional ? null : NaN;
    const n = Number(value);
    return Number.isFinite(n) && n >= min && n <= max ? n : NaN;
  }
  function estimate(data, input) {
    const errors = {};
    const users = numeric(input.users, 1, 20);
    const storageTb = numeric(input.storageTb, 0, 100);
    if (!Number.isInteger(users))
      errors.users = "Choose a whole number of users from 1 to 20.";
    if (!Number.isFinite(storageTb))
      errors.storageTb = "Enter a storage amount from 0 to 100 TB.";
    const playback = input.playback || "direct";
    if (!["direct", "hardware", "software"].includes(playback))
      errors.playback = "Choose a playback mode.";
    const quoteKeys = [
      "server",
      "includedGb",
      "storageRate",
      "backupRate",
      "network",
      "extras",
      "management",
    ];
    const quotes = {};
    for (const key of quoteKeys) {
      const maximum = key === "includedGb" ? 1000000 : 100000;
      quotes[key] = numeric(input.quotes?.[key], 0, maximum, true);
      if (Number.isNaN(quotes[key]))
        errors[key] =
          `Use a number from 0 to ${maximum.toLocaleString("en-US")}, or leave this quote empty.`;
    }
    if (Object.keys(errors).length) return { status: "invalid", errors };
    const picked = data.apps.filter((app) =>
      (input.apps || []).includes(app.id),
    );
    if (!picked.length) return { status: "empty", errors: {} };
    const assumptions = data.assumptions;
    const scale = Math.min(1 + (users - 1) * 0.08, 2);
    const allowances = picked.map((app) => ({
      ...app,
      ramMb: app.id === "immich" && input.ml === false ? 3072 : app.ramMb,
    }));
    const serviceRamMb = allowances.reduce(
      (sum, app) => sum + app.ramMb * scale,
      0,
    );
    const ramBeforeFloor =
      ((assumptions.osRamMb + serviceRamMb) / 1024) *
      assumptions.memoryHeadroom;
    const officialRamFloor = Math.max(
      0,
      ...picked.map((app) =>
        app.id === "immich" && input.ml === false
          ? 4
          : app.recommendedRamGb || app.minimumRamGb || 0,
      ),
    );
    const ramGb = Math.max(
      2,
      Math.ceil(ramBeforeFloor / 2) * 2,
      officialRamFloor,
    );
    const cpu = Math.max(
      1,
      Math.ceil(picked.reduce((sum, app) => sum + app.cpu * scale, 0)),
      ...picked.map((app) => app.recommendedCpu || app.minimumCpu || 0),
    );
    const appDiskGb = picked.reduce((sum, app) => sum + app.diskGb, 0);
    const photoOverhead = picked.some((app) => app.id === "immich")
      ? storageTb * 1000 * 0.2
      : 0;
    const usedGb = Math.ceil(appDiskGb + storageTb * 1000 + photoOverhead);
    const primaryGb = Math.ceil(usedGb * assumptions.storageHeadroom);
    const backupGb = usedGb;
    const video = picked.some((app) => app.video);
    const needsHardware = video && playback === "hardware";
    const softwareUnspecified = video && playback === "software";
    const oversized =
      ramGb > assumptions.maxStarterRamGb || cpu > assumptions.maxStarterCpu;
    const lines = [
      { id: "server", label: "Server", cost: quotes.server },
      {
        id: "storage",
        label: "Additional primary storage",
        cost:
          quotes.includedGb == null
            ? null
            : Math.max(0, primaryGb - quotes.includedGb) === 0
              ? 0
              : quotes.storageRate == null
                ? null
                : Math.max(0, primaryGb - quotes.includedGb) *
                  quotes.storageRate,
      },
      {
        id: "backup",
        label: "One full backup copy",
        cost: quotes.backupRate == null ? null : backupGb * quotes.backupRate,
      },
      { id: "network", label: "Transfer / egress", cost: quotes.network },
      { id: "extras", label: "Domain, licenses & taxes", cost: quotes.extras },
      {
        id: "management",
        label: "Management / other",
        cost: quotes.management,
      },
    ];
    const unknown = lines
      .filter((line) => line.cost == null)
      .map((line) => line.label);
    const known = lines.filter((line) => line.cost != null);
    const subtotal = known.length
      ? known.reduce((sum, line) => sum + line.cost, 0)
      : null;
    return {
      status: "ready",
      picked,
      allowances,
      users,
      storageTb,
      scale,
      ramGb,
      cpu,
      ramBeforeFloor,
      officialRamFloor,
      serviceRamMb,
      appDiskGb,
      photoOverhead,
      usedGb,
      primaryGb,
      backupGb,
      needsHardware,
      softwareUnspecified,
      oversized,
      quotes,
      lines,
      unknown,
      subtotal,
      complete: unknown.length === 0,
    };
  }
  function storage(gb) {
    return gb >= 1000
      ? `${(gb / 1000).toFixed(2).replace(/0+$/, "").replace(/\.$/, "")} TB`
      : `${gb} GB`;
  }
  return { estimate, storage };
});
