export const STORAGE_KEY = "nexus-theme";

export function getSystemTheme() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function getStoredTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return getSystemTheme();
}

/** Apply theme to <html> — used by inline boot script and React */
export function applyTheme(theme) {
  const root = document.documentElement;
  const isDark = theme === "dark";

  root.setAttribute("data-theme", theme);
  root.classList.toggle("dark", isDark);
  root.style.colorScheme = isDark ? "dark" : "light";

  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", isDark ? "#0a0d12" : "#f8fafc");
}
