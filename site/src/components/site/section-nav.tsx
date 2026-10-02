"use client";

import { useEffect, useRef, useState } from "react";
import { Icon } from "@/components/site/icon";
import { ThemeToggle } from "@/components/site/theme";

type Section = { id: string; label: string };

// Which section is on screen: an IntersectionObserver watches a band near the top of the window (no scroll
// listener). The footer coming into view marks the last section, which is often too short to reach the band.
function useActiveSection(sections: Section[]) {
  const [active, setActive] = useState(sections[0]?.id ?? "");

  useEffect(() => {
    const els = sections.map((s) => document.getElementById(s.id)).filter((e): e is HTMLElement => !!e);
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setActive(e.target.id);
      },
      { rootMargin: "-25% 0px -70% 0px" },
    );
    els.forEach((el) => io.observe(el));

    const footer = document.querySelector("footer");
    const last = sections[sections.length - 1]?.id;
    const end = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting) && last) setActive(last);
    });
    if (footer) end.observe(footer);

    return () => {
      io.disconnect();
      end.disconnect();
    };
  }, [sections]);

  return active;
}

function SectionLinks({
  sections,
  active,
  onPick,
}: {
  sections: Section[];
  active: string;
  onPick?: () => void;
}) {
  return (
    <ol className="space-y-1">
      {sections.map((s) => {
        const on = s.id === active;
        return (
          <li key={s.id}>
            <a
              href={`#${s.id}`}
              onClick={onPick}
              aria-current={on ? "location" : undefined}
              className={`flex items-center gap-2 py-1.5 font-pixel text-base leading-tight transition-colors ${
                on ? "text-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <span aria-hidden="true" className={`shrink-0 text-brand ${on ? "opacity-100" : "opacity-0"}`}>
                <Icon name="play" className="size-4" />
              </span>
              {s.label}
            </a>
          </li>
        );
      })}
    </ol>
  );
}

// Desktop: a sticky menu on the right that follows the page, like a game menu with a cursor.
export function SectionRail({ sections, cta }: { sections: Section[]; cta: { label: string; href: string } }) {
  const active = useActiveSection(sections);
  return (
    <nav aria-label="On this page" className="sticky top-16 max-h-[calc(100dvh-4rem)] overflow-y-auto px-7 py-10">
      <p className="font-pixel text-sm text-muted-foreground">On this page</p>
      <div className="mt-4">
        <SectionLinks sections={sections} active={active} />
      </div>
      <a
        href={cta.href}
        className="mt-8 inline-flex items-center gap-2 bg-primary px-4 py-2.5 font-pixel text-base text-primary-foreground transition-transform active:translate-y-px"
      >
        {cta.label}
        <Icon name="arrow-right" className="size-4" />
      </a>
    </nav>
  );
}

// Small screens: a Menu button in the header opens the same list.
export function MobileMenu({ sections }: { sections: Section[] }) {
  const [open, setOpen] = useState(false);
  const active = useActiveSection(sections);
  const panel = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        button.current?.focus();
      }
    };
    const onClick = (e: MouseEvent) => {
      const t = e.target as Node;
      if (!panel.current?.contains(t) && !button.current?.contains(t)) setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("click", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("click", onClick);
    };
  }, [open]);

  return (
    <div className="xl:hidden">
      <button
        ref={button}
        type="button"
        aria-expanded={open}
        aria-controls="section-menu"
        onClick={() => setOpen((v) => !v)}
        className="flex h-9 items-center gap-2 border-2 border-foreground/80 px-3 font-pixel text-base"
      >
        <Icon name={open ? "close" : "menu"} className="size-5" />
        <span className="max-[379px]:sr-only">Menu</span>
      </button>
      <div
        ref={panel}
        id="section-menu"
        hidden={!open}
        className="absolute inset-x-0 top-full border-b-4 border-line-soft bg-background px-4 py-6 sm:px-6"
      >
        <nav aria-label="On this page" className="mx-auto max-w-6xl columns-1 min-[480px]:columns-2">
          <SectionLinks sections={sections} active={active} onPick={() => setOpen(false)} />
        </nav>
        <div className="mx-auto mt-6 flex max-w-6xl items-center gap-4 sm:hidden">
          <span className="font-pixel text-base text-muted-foreground">Theme</span>
          <ThemeToggle />
        </div>
      </div>
    </div>
  );
}
