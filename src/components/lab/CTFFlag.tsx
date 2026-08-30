import { useState } from "react";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

interface CTFFlagProps {
  flag: string;
  revealed: boolean;
  label?: string;
}

/** Animated CTF flag reveal — shows when the learner completes a practical challenge. */
export function CTFFlag({ flag, revealed, label = "Flag Captured!" }: CTFFlagProps) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard?.writeText(flag).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  if (!revealed) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-dashed border-warning/30 bg-warning/5 px-4 py-3">
        <Icon name="flag" size={18} className="text-warning/60" />
        <div>
          <div className="font-mono text-[10px] uppercase tracking-widest text-warning/60">
            CTF Flag
          </div>
          <div className="mt-0.5 font-mono text-sm text-muted-foreground">
            Complete the challenge to reveal the flag
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-pop-in rounded-xl border border-success/40 bg-success/10 px-4 py-3">
      <div className="flex items-center gap-2">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-success/20 text-success">
          <Icon name="flag" size={18} />
        </span>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-widest text-success">
            {label}
          </div>
          <div className="mt-0.5 flex items-center gap-2">
            <code className="rounded-md bg-background/60 px-2 py-0.5 font-mono text-sm font-semibold text-success">
              {flag}
            </code>
            <button
              onClick={copy}
              className="rounded-md px-1.5 py-0.5 font-mono text-[10px] uppercase text-success/70 hover:bg-success/10 hover:text-success"
            >
              <Icon name={copied ? "check" : "copy"} size={12} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
