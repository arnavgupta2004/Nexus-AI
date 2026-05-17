import { useLayoutEffect, useState } from "react";
import { ThemeContext } from "./themeContext";
import { applyTheme, getStoredTheme, STORAGE_KEY } from "../lib/theme";

function readThemeFromDocument() {
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr === "light" || attr === "dark") return attr;
  return getStoredTheme();
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(readThemeFromDocument);

  useLayoutEffect(() => {
    applyTheme(theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  };

  const setLight = () => setTheme("light");
  const setDark = () => setTheme("dark");

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setLight, setDark }}>
      {children}
    </ThemeContext.Provider>
  );
}
