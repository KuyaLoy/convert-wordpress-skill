"use client";

import { ThemeProvider as NextThemes, useTheme } from "next-themes";
import { useSyncExternalStore } from "react";
import { Icon } from "@/components/site/icon";

// Auto (the visitor's system setting) is the default; Light and Dark can be pinned and are remembered.
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemes attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      {children}
    </NextThemes>
  );
}

const OPTIONS = [
  { value: "system", label: "Auto", icon: "monitor" },
  { value: "light", label: "Light", icon: "sun" },
  { value: "dark", label: "Dark", icon: "moon" },
] as const;

// true once the page runs in the browser, so the switch never shows a wrong state while the page loads
const subscribe = () => () => {};
function useMounted() {
  return useSyncExternalStore(subscribe, () => true, () => false);
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const mounted = useMounted();
  const current = mounted ? (theme ?? "system") : null;

  return (
    <div role="group" aria-label="Colour theme" className="flex border-2 border-foreground/80">
      {OPTIONS.map((o) => {
        const on = current === o.value;
        return (
          <button
            key={o.value}
            type="button"
            title={o.label}
            aria-label={`${o.label} theme`}
            aria-pressed={on}
            onClick={() => setTheme(o.value)}
            className={`grid size-9 place-items-center transition-colors ${
              on ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground"
            }`}
          >
            <Icon name={o.icon} className="size-5" />
          </button>
        );
      })}
    </div>
  );
}
