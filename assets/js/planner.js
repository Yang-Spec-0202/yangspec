(() => {
  "use strict";
  const root = document.querySelector("[data-planner]");
  if (!root) return;
  const data = JSON.parse(document.getElementById("planner-data").textContent);
  const model = window.YangSpecPlanner;
  const form = root.querySelector("form");
  const status = document.getElementById("planner-status");
  const result = document.getElementById("result-content");
  const summary = document.getElementById("result-summary");
  const quoteFields = [
    "server",
    "includedGb",
    "storageRate",
    "backupRate",
    "network",
    "extras",
    "management",
  ];
  let current;
  let announceTimer;
  const money = (value) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(value);
  const node = (tag, className, text) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text != null) el.textContent = text;
    return el;
  };
  function read() {
    return {
      apps: [...form.querySelectorAll("[data-app]:checked")].map(
        (el) => el.value,
      ),
      users: form.elements.users.value,
      storageTb: form.elements.storageTb.value,
      playback: form.elements.playback.value,
      ml: form.elements.ml.checked,
      quotes: Object.fromEntries(
        quoteFields.map((key) => [key, form.elements[key].value]),
      ),
    };
  }
  function announce(text) {
    clearTimeout(announceTimer);
    announceTimer = setTimeout(() => {
      status.textContent = text;
    }, 300);
  }
  function update() {
    const input = read();
    current = model.estimate(data, input);
    const hasVideo = input.apps.some(
      (id) => data.apps.find((app) => app.id === id)?.video,
    );
    document.getElementById("playback-field").hidden = !hasVideo;
    document.getElementById("ml-field").hidden = !input.apps.includes("immich");
    form
      .querySelectorAll("[data-app]")
      .forEach((el) =>
        el.closest("label").classList.toggle("is-selected", el.checked),
      );
    form.querySelectorAll("[data-group]").forEach((group) => {
      group.querySelector("[data-count]").textContent =
        group.querySelectorAll("input:checked").length;
    });
    form.querySelectorAll("[data-preset]").forEach((button) => {
      const p = data.presets.find((item) => item.id === button.dataset.preset);
      button.setAttribute(
        "aria-pressed",
        String(
          p.apps.length === input.apps.length &&
            p.apps.every((id) => input.apps.includes(id)) &&
            input.storageTb === String(p.storageTb),
        ),
      );
    });
    for (const el of form.querySelectorAll("[data-validated]")) {
      const error = current.errors?.[el.name];
      el.setAttribute("aria-invalid", String(Boolean(error)));
      const message = document.getElementById(`${el.name}-error`);
      message.textContent = error || "";
      message.hidden = !error;
    }
    result.replaceChildren();
    document.getElementById("copy-fallback").hidden = true;
    document.getElementById("plan-text").value = "";
    document.getElementById("copy-plan").disabled = current.status !== "ready";
    if (current.status === "invalid") {
      result.append(
        node("p", "result-state", "Check the highlighted inputs."),
        node(
          "p",
          "muted",
          "Your previous figures are hidden until every input is valid.",
        ),
      );
      summary.textContent = "Check your inputs";
      announce("Plan not updated. Check the highlighted inputs.");
      return;
    }
    if (current.status === "empty") {
      const empty = node("div", "result-empty");
      const symbol = node("span", "empty-symbol", "+");
      symbol.setAttribute("aria-hidden", "true");
      empty.append(
        symbol,
        node("h3", "", "A little planning goes a long way."),
        node(
          "p",
          "muted",
          "Choose a starting point or pick your first app. Your capacity and cost breakdown will appear here.",
        ),
      );
      result.append(empty);
      summary.textContent = "Choose an app to begin";
      announce("No apps selected. Choose an app to begin.");
      return;
    }
    result.append(
      node(
        "p",
        "result-badge",
        current.oversized
          ? "Custom sizing needed"
          : current.softwareUnspecified
            ? "Transcoding sizing needed"
            : "Personal-use planning target",
      ),
    );
    const metrics = node("dl", "plan-metrics");
    for (const [label, value, unit] of [
      ["Memory", current.ramGb, "GB"],
      ["Compute", current.cpu, "cores"],
      ["Primary storage", model.storage(current.primaryGb), ""],
    ]) {
      const item = node("div", "metric");
      item.append(node("dt", "", label));
      const number = node("dd", "", value);
      number.append(node("span", "metric-unit", unit));
      item.append(number);
      metrics.append(item);
    }
    result.append(metrics);
    const map = node("div", "workload-map");
    const apps = node("div", "workload-apps");
    current.picked.forEach((app) =>
      apps.append(node("span", "workload-tag", app.name)),
    );
    map.append(
      apps,
      node("span", "workload-connector", "↓"),
      node(
        "p",
        "workload-host",
        current.needsHardware
          ? "Host + compatible GPU / iGPU"
          : "Your planned host",
      ),
      node("span", "workload-connector", "↓"),
      node(
        "p",
        "workload-backup",
        `${model.storage(current.backupGb)} backup · separate location`,
      ),
    );
    result.append(map);
    const warnings = [];
    if (current.oversized)
      warnings.push(
        "This is beyond our 32 GB / 8-core starter range. No matching plan is implied; use workload-specific sizing.",
      );
    if (current.needsHardware)
      warnings.push(
        "Hardware transcoding needs a compatible GPU or iGPU, codecs and device access. These CPU/RAM figures do not establish support on a VPS. Confirm the device and passthrough before buying.",
      );
    if (current.softwareUnspecified)
      warnings.push(
        "Software transcoding is not sized here. Resolution, codec, tone mapping and simultaneous streams need a real test before choosing CPU capacity.",
      );
    if (current.storageTb >= 1)
      warnings.push(
        "At this library size, compare attached storage, a storage-focused server and a home server. Check filesystem compatibility and backup costs before buying.",
      );
    if (
      current.picked.some((app) =>
        ["minio", "matrix", "grafana"].includes(app.id),
      )
    )
      warnings.push(
        "Infrastructure allowances cover a small evaluation or personal setup. Retention, federation and production resilience need separate sizing.",
      );
    if (warnings.length) {
      const list = node("ul", "plan-warnings");
      warnings.forEach((text) => list.append(node("li", "", text)));
      result.append(list);
    }
    const costs = node("section", "cost-breakdown");
    const costHeader = node("div", "cost-heading");
    costHeader.append(
      node("h3", "", "Monthly cost"),
      node("span", "cost-currency", "USD · your quotes"),
    );
    costs.append(costHeader);
    const total = node(
      "p",
      "cost-total",
      current.subtotal == null ? "Add your quotes" : money(current.subtotal),
    );
    if (current.subtotal != null)
      total.append(
        node("span", "", current.complete ? "/ month" : "known subtotal"),
      );
    costs.append(total);
    const list = node("dl", "cost-lines");
    current.lines.forEach((line) => {
      const row = node("div", "");
      row.append(
        node("dt", "", line.label),
        node(
          "dd",
          line.cost == null ? "unquoted" : "",
          line.cost == null ? "Not quoted" : money(line.cost),
        ),
      );
      list.append(row);
    });
    costs.append(
      list,
      node(
        "p",
        "cost-note",
        current.complete
          ? "Quote-based total, not a provider offer. Verify renewal, capacity and currency before purchase. Your maintenance time and hardware purchases are outside this monthly total."
          : "An empty quote is unknown, not free. Enter 0 only for a confirmed included or zero-cost item.",
      ),
    );
    result.append(costs);
    const why = node("details", "result-details");
    why.append(node("summary", "", "Why this size?"));
    why.append(
      node(
        "p",
        "",
        `Service allowances + ${data.assumptions.osRamMb / 1024} GB for OS/runtime, scaled for ${current.users} user${current.users === 1 ? "" : "s"}, then 25% memory headroom. Capacity rounds up to 2 GB increments and respects documented whole-host guidance where available.`,
      ),
    );
    why.append(
      node(
        "p",
        "",
        `Primary storage includes ${current.appDiskGb} GB of application/data allowance, your library${current.photoOverhead ? ", 20% for Immich thumbnails/video" : ""}, and 20% spare capacity. Backup is one full data copy; versions and retention require more. Storage uses decimal GB/TB.`,
      ),
    );
    const sources = node("ul", "source-list");
    current.picked.forEach((app) => {
      const li = node("li", "");
      const a = node("a", "", app.name);
      a.href = app.source;
      li.append(a, node("span", "", ` — ${app.context}`));
      sources.append(li);
    });
    why.append(
      sources,
      node(
        "p",
        "muted",
        `Model reviewed ${data.reviewed}. Service allowances are YangSpec estimates, not benchmarks or official minima. CPU cores on a shared VPS are not equivalent to dedicated physical cores.`,
      ),
    );
    result.append(why);
    summary.textContent = `${current.ramGb} GB · ${current.cpu} cores · ${model.storage(current.primaryGb)}`;
    announce(
      `Plan updated for ${current.picked.length} app${current.picked.length === 1 ? "" : "s"}: ${summary.textContent}. ${current.oversized ? "Custom sizing needed." : ""} ${current.subtotal == null ? "Monthly costs not quoted." : `${current.complete ? "Monthly total" : "Known monthly subtotal"} ${money(current.subtotal)}.`}`,
    );
  }
  function preset(id) {
    const p = data.presets.find((item) => item.id === id);
    if (!p) return;
    form.querySelectorAll("[data-app]").forEach((el) => {
      el.checked = p.apps.includes(el.value);
    });
    form.elements.storageTb.value = p.storageTb;
    form.elements.users.value = "1";
    form.elements.playback.value = "direct";
    form.elements.ml.checked = true;
    for (const group of form.querySelectorAll("[data-group]"))
      group.open = group.querySelector("input:checked") != null;
    update();
  }
  form.addEventListener("submit", (event) => event.preventDefault());
  form.addEventListener("input", update);
  form.addEventListener("change", update);
  root
    .querySelectorAll("[data-preset]")
    .forEach((button) =>
      button.addEventListener("click", () => preset(button.dataset.preset)),
    );
  document.getElementById("clear-plan").addEventListener("click", () => {
    form.reset();
    for (const group of form.querySelectorAll("[data-group]"))
      group.open = group.dataset.group === "everyday";
    form.querySelector(".quote-panel").open = false;
    update();
  });
  document.getElementById("copy-plan").addEventListener("click", async () => {
    if (current.status !== "ready") return;
    const text = [
      "YangSpec personal-use plan",
      `Apps: ${current.picked.map((app) => app.name).join(", ")}`,
      `Target: ${summary.textContent}`,
      `Backup: ${model.storage(current.backupGb)} for one full copy`,
      `Playback: ${read().playback}; Immich ML: ${read().ml ? "on" : "off"}`,
      `Cost: ${current.subtotal == null ? "not quoted" : `${money(current.subtotal)} ${current.complete ? "per month" : "known monthly subtotal"}`}`,
      `Unquoted: ${current.unknown.join(", ") || "none"}`,
      `Model reviewed: ${data.reviewed}`,
      "Planning estimates, not benchmark or guaranteed provider compatibility.",
      "https://yangspec.com/tools/selfhost-planner/",
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      announce("Plan copied to clipboard.");
      const button = document.getElementById("copy-plan");
      button.textContent = "Copied ✓";
      setTimeout(() => {
        button.textContent = "Copy plan";
      }, 2000);
    } catch {
      const fallback = document.getElementById("copy-fallback");
      fallback.hidden = false;
      fallback.querySelector("textarea").value = text;
      fallback.querySelector("textarea").focus();
      fallback.querySelector("textarea").select();
      announce("Clipboard unavailable. Select and copy the plan text below.");
    }
  });
  const resultPanel = document.getElementById("result");
  const resultLink = root.querySelector("[data-view-result]");
  resultLink.addEventListener("click", () => {
    document
      .querySelector(resultLink.getAttribute("href"))
      .focus({ preventScroll: true });
  });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(
      (entries) => {
        const inResult = entries[0].isIntersecting;
        resultLink.setAttribute(
          "href",
          inResult ? "#planner-inputs" : "#result",
        );
        resultLink.querySelector("[data-result-action]").textContent = inResult
          ? "Edit choices ↑"
          : "View plan ↗";
      },
      { rootMargin: "-28px 0px -50% 0px" },
    ).observe(resultPanel);
  }
  if ("ResizeObserver" in window) {
    const setSticky = () =>
      resultPanel.classList.toggle(
        "can-stick",
        innerWidth > 760 && resultPanel.offsetHeight < innerHeight - 48,
      );
    new ResizeObserver(setSticky).observe(resultPanel);
    window.addEventListener("resize", setSticky);
    setSticky();
  }
  preset(new URLSearchParams(location.search).get("preset"));
  update();
})();
