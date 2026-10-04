(() => {
  const button = document.getElementById("theme-toggle");
  if (!button) return;
  const updateLabel = () => {
    button.setAttribute(
      "aria-label",
      `Switch to ${document.documentElement.dataset.theme === "dark" ? "light" : "dark"} theme`,
    );
  };
  button.addEventListener("click", () => {
    const next =
      document.documentElement.dataset.theme === "dark" ? "light" : "dark";
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
