(() => {
  const demo = document.querySelector("[data-home-demo]");
  if (!demo) return;
  const data = JSON.parse(
    document.getElementById("home-planner-data").textContent,
  );
  const buttons = [...demo.querySelectorAll("[data-demo]")];
  function select(id, announce = true) {
    const preset = data.presets.find((p) => p.id === id);
    const result = YangSpecPlanner.estimate(data, {
      apps: preset.apps,
      users: 1,
      storageTb: preset.storageTb,
      playback: "direct",
      ml: true,
    });
    buttons.forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.demo === id)),
    );
    document.getElementById("demo-apps").textContent = result.picked
      .map((a) => a.name)
      .join(" · ");
    for (const [target, value, unit] of [
      ["demo-ram", result.ramGb, "GB"],
      ["demo-cpu", result.cpu, result.cpu === 1 ? "core" : "cores"],
      ["demo-storage", YangSpecPlanner.storage(result.primaryGb), ""],
    ]) {
      const el = document.getElementById(target);
      el.textContent = value + " ";
      const span = document.createElement("span");
      span.textContent = unit;
      el.append(span);
    }
    document.getElementById("demo-link").search = `?preset=${id}`;
    if (announce)
      document.getElementById("demo-status").textContent =
        `${preset.name}: ${result.ramGb} GB memory, ${result.cpu} cores, ${YangSpecPlanner.storage(result.primaryGb)} primary storage.`;
  }
  buttons.forEach((button) =>
    button.addEventListener("click", () => select(button.dataset.demo)),
  );
  select("essentials", false);
})();
