"use client";

import { useState } from "react";

// Copies a command. Says "Copied" for two seconds; falls back to selecting the text if the clipboard is blocked.
export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [state, setState] = useState<"idle" | "done" | "failed">("idle");

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setState("done");
    } catch {
      setState("failed");
    }
    window.setTimeout(() => setState("idle"), 2000);
  }

  return (
    <button
      type="button"
      onClick={copy}
      className="shrink-0 bg-secondary px-3 py-2 font-pixel text-sm text-foreground transition-colors hover:bg-primary hover:text-primary-foreground active:translate-y-px"
      aria-label={`${label}: ${text}`}
    >
      <span aria-live="polite">{state === "done" ? "Copied" : state === "failed" ? "Select it" : label}</span>
    </button>
  );
}

export function CodeLine({ text }: { text: string }) {
  return (
    <div className="pixel-frame flex items-center gap-3 bg-panel py-1 pr-1 pl-4 [--frame:#3a3a3a]">
      <code className="min-w-0 flex-1 py-2 text-[0.95rem] [overflow-wrap:anywhere] whitespace-pre-wrap text-foreground select-all">
        {text}
      </code>
      <CopyButton text={text} />
    </div>
  );
}
