import { useState } from "react";
import { useApp } from "../../context/AppContext";
import type { Lab } from "../../lib/types";
import { HintEngine } from "../../lib/engine";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

export function HintPanel({ lab }: { lab: Lab }) {
  const { useHint, labProgress } = useApp();
  const progress = labProgress(lab.id);
  const revealedFromState = progress.hintsUsed;
  const [revealed, setRevealed] = useState(Math.min(revealedFromState, lab.hints.length));
  const [open, setOpen] = useState(false);
  const suggestion = HintEngine.suggestHint(lab, progress);

  const reveal = () => {
    if (revealed >= lab.hints.length) return;
    setRevealed((r) => r + 1);
    useHint(lab.id);
  };

  return (
    <div className="rounded-2xl border border-border bg-card">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 p-4 text-left"
        aria-expanded={open}
      >
        <span className="grid h-9 w-9 place-items-center rounded-lg bg-warning/10 text-warning">
          <Icon name="lightbulb" size={18} />
        </span>
        <span className="flex-1">
          <span className="block text-sm font-semibold text-foreground">Need a clue?</span>
          <span className="block font-mono text-[11px] text-muted-foreground">
            {revealed}/{lab.hints.length} hints revealed · each costs points
          </span>
        </span>
        <Icon name="chevron-down" size={18} className={cx("text-subtle transition-transform", open && "rotate-180")} />
      </button>

      {suggestion.offer && !open && (
        <div className="mx-4 mb-3 flex items-start gap-2 rounded-lg border border-cyan/30 bg-cyan/5 p-2.5 text-xs text-cyan">
          <Icon name="sparkles" size={13} className="mt-0.5 shrink-0" />
          <span>{suggestion.reason}</span>
        </div>
      )}

      {open && (
        <div className="space-y-3 border-t border-border p-4">
          {lab.hints.slice(0, revealed).map((h, i) => (
            <div
              key={i}
              className="animate-fade-slide rounded-xl border border-warning/20 bg-warning/5 p-3"
              style={{ animationDelay: `${i * 70}ms` }}
            >
              <div className="mb-1 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-warning">
                <Icon name="lightbulb" size={12} /> Hint {i + 1}
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{h}</p>
            </div>
          ))}
          {revealed < lab.hints.length ? (
            <button
              onClick={reveal}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-warning/40 py-2.5 text-sm font-medium text-warning transition-colors hover:bg-warning/5"
            >
              <Icon name="plus" size={15} />
              Reveal hint {revealed + 1}
            </button>
          ) : (
            <div className="text-center font-mono text-[11px] text-subtle">
              All hints revealed. Trust your investigation.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
