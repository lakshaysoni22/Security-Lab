import { useState } from "react";
import { useApp } from "../../context/AppContext";
import type { Lab } from "../../lib/types";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

const CATEGORIES = ["Observation", "Anomaly", "Payload", "Header", "Config"];

export function EvidencePanel({ lab }: { lab: Lab }) {
  const { labProgress, addEvidence, removeEvidence } = useApp();
  const evidence = labProgress(lab.id).evidence;
  const [text, setText] = useState("");
  const [cat, setCat] = useState(CATEGORIES[0]);

  const add = () => {
    if (!text.trim()) return;
    addEvidence(lab.id, text.trim(), cat);
    setText("");
  };

  return (
    <div className="rounded-2xl border border-border bg-card">
      <div className="flex items-center gap-3 border-b border-border p-4">
        <span className="grid h-9 w-9 place-items-center rounded-lg bg-cyan/10 text-cyan">
          <Icon name="search" size={18} />
        </span>
        <div className="flex-1">
          <div className="text-sm font-semibold text-foreground">Evidence Log</div>
          <div className="font-mono text-[11px] text-muted-foreground">
            {evidence.length} item(s) recorded
          </div>
        </div>
      </div>

      <div className="max-h-64 space-y-2.5 overflow-auto p-4 no-scrollbar">
        {evidence.length === 0 && (
          <p className="py-4 text-center text-xs text-subtle">
            Record what you observe as you investigate.
          </p>
        )}
        {evidence.map((e) => (
          <div key={e.id} className="animate-pop-in rounded-xl border border-border bg-background p-3">
            <div className="mb-1 flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase tracking-widest text-cyan">
                Evidence #{String(e.index).padStart(2, "0")} · {e.category}
              </span>
              <button
                onClick={() => removeEvidence(lab.id, e.id)}
                className="text-subtle hover:text-danger"
                aria-label="Remove evidence"
              >
                <Icon name="trash" size={13} />
              </button>
            </div>
            <p className="text-sm text-foreground">{e.observation}</p>
            <div className="mt-1 font-mono text-[10px] text-subtle">
              {new Date(e.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-2 border-t border-border p-4">
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setCat(c)}
              className={cx(
                "rounded-md px-2 py-1 font-mono text-[10px] uppercase tracking-wider transition-colors",
                cat === c ? "bg-cyan/15 text-cyan" : "bg-muted/50 text-muted-foreground hover:text-foreground",
              )}
            >
              {c}
            </button>
          ))}
        </div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Log an observation…"
          rows={2}
          className="w-full resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-cyan/50"
        />
        <button
          onClick={add}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-muted py-2 text-sm font-medium text-foreground hover:bg-elevated"
        >
          <Icon name="plus" size={15} /> Add evidence
        </button>
      </div>
    </div>
  );
}
