(() => {
  const button = document.getElementById("theme-toggle");
  if (!button) return;
  // 名称描述“点击后的动作”，与图标表示的目标主题一致；当前状态由
  // html[data-theme] 与图标共同表达，避免 aria-pressed 与动作名称打架。
  const labels = { light: "切换为深色主题", dark: "切换为浅色主题" };
  const currentTheme = () =>
    document.documentElement.dataset.theme === "dark" ? "dark" : "light";
  const updateLabel = () => {
    const label = labels[currentTheme()];
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
  };
  button.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("pref-theme", next);
    } catch {
      /* Preference storage is optional. */
    }
    updateLabel();
  });
  updateLabel();
})();
