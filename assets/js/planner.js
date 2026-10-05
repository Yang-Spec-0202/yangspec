(() => {
  "use strict";
  const root = document.querySelector("[data-planner]");
  if (!root) return;
  const data = JSON.parse(document.getElementById("planner-data").textContent);
  const model = window.YangSpecPlanner;
  const form = root.querySelector("form");
  const status = document.getElementById("planner-status");
  const result = document.getElementById("result-content");
  const nextStep = document.getElementById("planner-next-step");
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
  let copyTimer;
  let revision = 0;
  let explanationOpen = false;
  let lastInputState;
  const copyButton = document.getElementById("copy-plan");
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
  function nextStepFor(plan) {
    if (plan.status !== "ready")
      return {
        title:
          plan.status === "empty"
            ? "Start with your apps"
            : "Fix the inputs first",
        text:
          plan.status === "empty"
            ? "Choose a starting point or an app before comparing hosts. No package has been matched."
            : "Correct the highlighted fields before using a capacity estimate or comparing hosts.",
        links: [["Go to your choices", "#planner-inputs"]],
      };
    if (plan.oversized)
      return {
        title: "Size this workload separately",
        text: "This exceeds the starter range. Measure your workload and check each app's requirements; the small VPS comparison is not a match for this plan.",
        links: [
          ["Read the sizing limits", "/posts/how-much-ram-to-self-host/"],
        ],
      };
    const storageLink = [
      "Plan storage and backups",
      "#storage-and-a-real-backup",
    ];
    const hasImmich = plan.picked.some((app) => app.id === "immich");
    const immichLink = [
      "Read the Immich storage and cost guide",
      "/posts/immich-2tb-hosting-cost/",
    ];
    const hasJellyfin = plan.picked.some((app) => app.id === "jellyfin");
    const jellyfinLink = [
      "Compare Jellyfin hosting and playback",
      "/posts/jellyfin-vps-or-home-server/",
    ];
    const hasLibrary =
      plan.storageTb > 0 ||
      plan.primaryGb > 80 ||
      plan.picked.some((app) => app.photo);
    if (
      plan.softwareUnspecified ||
      plan.needsHardware ||
      plan.picked.some((app) => app.video)
    )
      return {
        title: plan.softwareUnspecified
          ? "Test software transcoding first"
          : plan.needsHardware
            ? "Verify the video device first"
            : "Check Direct Play compatibility",
        text: plan.softwareUnspecified
          ? "CPU transcoding capacity is not estimated. Test your codecs, resolution and simultaneous streams before choosing a host."
          : plan.needsHardware
            ? "These CPU and RAM figures do not prove GPU access. Confirm the device, codecs, drivers and passthrough before buying."
            : "Confirm that your clients can play the original codecs without conversion before relying on this target.",
        links: [
          ...(hasJellyfin ? [jellyfinLink] : []),
          ["Read the playback checks", "#playback-changes-the-decision"],
          ...(hasLibrary ? [storageLink] : []),
          ...(hasImmich ? [immichLink] : []),
        ],
      };
    if (plan.picked.some((app) => app.photo) || plan.primaryGb > 80)
      return {
        title: "Plan storage and recovery first",
        text: hasImmich
          ? "Use the Immich guide to compare a home host, attached cloud storage and an independent backup. Its worked example is a 2 TB library; adjust capacity and quotes for your plan. No provider package has been verified as a match."
          : "Compare usable primary storage and a separate backup, including generated files and restore needs. A small VPS disk is not automatically enough; compare attached storage, a storage-focused host and a home server.",
        links: [
          ...(hasImmich ? [immichLink] : []),
          storageLink,
          ["Compare the full cost", "/posts/self-hosting-vs-cloud-cost/"],
        ],
      };
    // A conservative guide scope, not a package match or provider ranking.
    if (
      plan.ramGb <= 4 &&
      plan.cpu <= 2 &&
      plan.picked.every((app) => app.ramMb <= 512 && app.group !== "advanced")
    )
      return {
        title: "Compare small VPS plans",
        text: "This light-app estimate is within the guide's small-capacity scope. Check the actual workload, usable disk, region and billing terms. No provider package has been verified as a match. Compare the whole bill, including storage, backup and other costs.",
        links: [
          [
            "Read the 2 GB / 4 GB comparison",
            "/posts/best-cheap-vps-for-self-hosting-2026/",
          ],
        ],
      };
    return {
      title: "Check the workload before choosing a host",
      text: "This stack is outside the light-app comparison's scope. Review each app's requirements and measure busy periods; a capacity estimate alone does not establish provider compatibility.",
      links: [
        ["Read the RAM and sizing guide", "/posts/how-much-ram-to-self-host/"],
      ],
    };
  }
  function renderNextStep(step) {
    const heading = node("h3", "", step.title);
    heading.id = "next-step-title";
    const links = node("div", "next-step-links");
    step.links.forEach(([label, href]) => {
      const link = node("a", "next-step-link", label);
      link.href = href;
      if (href === "#planner-inputs")
        link.addEventListener("click", () =>
          form.focus({ preventScroll: true }),
        );
      links.append(link);
    });
    nextStep.replaceChildren(heading, node("p", "", step.text), links);
  }
  function update(input = read()) {
    lastInputState = JSON.stringify(input);
    revision += 1;
    clearTimeout(copyTimer);
    copyButton.textContent = "Copy plan";
    current = model.estimate(data, input);
    const step = nextStepFor(current);
    renderNextStep(step);
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
    copyButton.disabled = current.status !== "ready";
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
      announce(
        "Plan not updated. Check the highlighted inputs. Next step: fix the inputs first.",
      );
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
      announce(
        "No apps selected. Next step: choose a starting point or an app before comparing hosts.",
      );
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
      ["Primary storage", ...model.storage(current.primaryGb).split(" ")],
    ]) {
      const item = node("div", "metric");
      item.append(node("dt", "", label));
      const number = node("dd", "", value);
      number.append(node("span", "metric-unit", unit));
      item.append(number);
      metrics.append(item);
    }
    result.append(metrics);
    const storage = node("section", "storage-explained");
    storage.append(node("h3", "", "Where the storage goes"));
    const bar = node("div", "storage-bar");
    bar.setAttribute("aria-hidden", "true");
    const parts = node("dl", "storage-parts");
    current.storageParts
      .filter((part) => part.gb > 0)
      .forEach((part) => {
        const segment = node("span", `storage-${part.id}`);
        segment.style.flexBasis = `${(part.gb / current.primaryGb) * 100}%`;
        bar.append(segment);
        const row = node("div", `storage-${part.id}`);
        row.append(
          node("dt", "", part.label),
          node("dd", "", model.storage(part.gb)),
        );
        parts.append(row);
      });
    storage.append(bar, parts);
    const backup = node("p", "storage-backup");
    backup.append(
      node("strong", "", `${model.storage(current.backupGb)} separate backup`),
      node(
        "span",
        "",
        "One full data copy, without spare space. Versions and retention need more.",
      ),
    );
    storage.append(backup);
    result.append(storage);
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
    if (!current.complete) {
      const coverage = node("p", "cost-coverage");
      coverage.append(
        node("strong", "", "Total monthly cost unknown"),
        node(
          "span",
          "",
          `${current.unknown.length} prices still missing. Add them to calculate the total.`,
        ),
      );
      costs.append(coverage);
    }
    const total = node(
      "p",
      "cost-total",
      current.subtotal == null ? "Add your quotes" : money(current.subtotal),
    );
    total.classList.toggle("is-long", total.textContent.length > 16);
    if (current.subtotal != null)
      total.append(
        node("span", "", current.complete ? "/ month" : "partial / month"),
      );
    costs.append(total);
    const priced = current.lines.length - current.unknown.length;
    const progress = node(
      "p",
      "quote-progress",
      `${priced} of ${current.lines.length} cost items priced`,
    );
    progress.classList.toggle("is-complete", current.complete);
    costs.append(progress);
    if (!current.complete && priced > 0) {
      costs.append(
        node(
          "p",
          "cost-included",
          `Counted in this amount: ${current.lines
            .filter((line) => line.cost != null)
            .map((line) => line.label)
            .join(", ")}.`,
        ),
      );
    }
    const list = node("dl", "cost-lines");
    current.lines.forEach((line) => {
      const row = node("div", "");
      row.append(
        node("dt", "", line.label),
        node(
          "dd",
          line.cost == null ? "unquoted" : "",
          line.cost == null ? "Price missing" : money(line.cost),
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
    why.open = explanationOpen;
    why.addEventListener("toggle", () => {
      if (why.isConnected) explanationOpen = why.open;
    });
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
      `Plan updated for ${current.picked.length} app${current.picked.length === 1 ? "" : "s"}: ${summary.textContent}. ${current.oversized ? "Custom sizing needed." : ""} ${current.subtotal == null ? "Monthly costs not quoted." : `${current.complete ? "Monthly total" : "Partial monthly cost"} ${money(current.subtotal)}.`} ${current.complete ? "" : `Total monthly cost unknown; ${current.unknown.length} prices still missing.`} Next step: ${step.title}.`,
    );
  }
  function preset(id) {
    const p = data.presets.find(
      (item) => item.id === (id === "photos-2tb" ? "photos" : id),
    );
    if (!p) return;
    form.querySelectorAll("[data-app]").forEach((el) => {
      el.checked = p.apps.includes(el.value);
    });
    form.elements.storageTb.value = id === "photos-2tb" ? 2 : p.storageTb;
    form.elements.users.value = "1";
    form.elements.playback.value = "direct";
    form.elements.ml.checked = true;
    for (const group of form.querySelectorAll("[data-group]"))
      group.open = group.querySelector("input:checked") != null;
    update();
  }
  form.addEventListener("submit", (event) => event.preventDefault());
  function updateFromForm() {
    const input = read();
    // Blur can emit change after input; keep the existing result and its focus.
    if (JSON.stringify(input) !== lastInputState) update(input);
  }
  form.addEventListener("input", updateFromForm);
  form.addEventListener("change", updateFromForm);
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
    explanationOpen = false;
    update();
  });
  copyButton.addEventListener("click", async () => {
    if (current.status !== "ready") return;
    const copiedRevision = revision;
    const input = read();
    const text = [
      "YangSpec personal-use plan",
      `Apps: ${current.picked.map((app) => app.name).join(", ")}`,
      `Target: ${summary.textContent}`,
      `Backup: ${model.storage(current.backupGb)} for one full copy`,
      ...current.storageParts
        .filter((part) => part.gb > 0)
        .map((part) => `${part.label}: ${model.storage(part.gb)}`),
      ...(current.picked.some((app) => app.video)
        ? [`Playback: ${input.playback}`]
        : []),
      ...(current.softwareUnspecified
        ? [
            "Software transcoding: not sized; the base CPU figure is not transcode capacity. Test codecs, resolution, tone mapping and simultaneous streams.",
          ]
        : current.needsHardware
          ? [
              "Hardware transcoding: GPU access and compatibility are unverified. Confirm the device, codecs, drivers and passthrough; CPU/RAM figures do not establish support.",
            ]
          : []),
      ...(input.apps.includes("immich")
        ? [`Immich ML: ${input.ml ? "on" : "off"}`]
        : []),
      `Cost: ${current.subtotal == null ? "not quoted" : `${money(current.subtotal)} per month${current.complete ? "" : " (partial)"}`}`,
      `Total monthly cost: ${current.complete ? `${money(current.subtotal)} per month from your quotes` : `unknown; ${current.unknown.length} prices still missing`}`,
      `Priced items: ${
        current.lines
          .filter((line) => line.cost != null)
          .map((line) => line.label)
          .join(", ") || "none"
      }`,
      `Unquoted: ${current.unknown.join(", ") || "none"}`,
      `Model reviewed: ${data.reviewed}`,
      "Planning estimates, not benchmark or guaranteed provider compatibility.",
      "https://yangspec.com/tools/selfhost-planner/",
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      if (copiedRevision !== revision) return;
      announce("Plan copied to clipboard.");
      copyButton.textContent = "Copied ✓";
      clearTimeout(copyTimer);
      copyTimer = setTimeout(() => {
        copyButton.textContent = "Copy plan";
      }, 2000);
    } catch {
      if (copiedRevision !== revision) return;
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
