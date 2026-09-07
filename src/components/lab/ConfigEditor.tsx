import { useState } from "react";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

export interface ConfigLine {
  key: string;
  insecureValue: string;
  secureValue: string;
  hint: string;
  severity: "critical" | "high" | "medium" | "low";
}

interface ConfigEditorProps {
  /** Title of the config file. */
  filename?: string;
  /** The configuration lines to edit. */
  configLines: ConfigLine[];
  /** Callback when all lines are fixed correctly. */
  onAllFixed?: () => void;
  /** Callback on any change with current score. */
  onProgress?: (fixed: number, total: number) => void;
  className?: string;
}

const SEV_BADGE: Record<string, string> = {
  critical: "bg-danger/15 text-danger border-danger/30",
  high: "bg-warning/15 text-warning border-warning/30",
  medium: "bg-cyan/15 text-cyan border-cyan/30",
  low: "bg-muted text-muted-foreground border-border",
};

/** Interactive config editor — the user fixes insecure values line by line. */
export function ConfigEditor({
  filename = ".env.production",
  configLines,
  onAllFixed,
  onProgress,
  className,
}: ConfigEditorProps) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(configLines.map((l) => [l.key, l.insecureValue])),
  );
  const [showHints, setShowHints] = useState<Record<string, boolean>>({});
  const [submitted, setSubmitted] = useState(false);

  const isFixed = (line: ConfigLine) => {
    const v = values[line.key]?.trim().toLowerCase();
    const s = line.secureValue.trim().toLowerCase();
    return v === s;
  };

  const fixedCount = configLines.filter(isFixed).length;
  const allFixed = fixedCount === configLines.length;
  const pct = Math.round((fixedCount / configLines.length) * 100);

  const handleChange = (key: string, val: string) => {
    const next = { ...values, [key]: val };
    setValues(next);
    const fixed = configLines.filter((l) => {
      const v = next[l.key]?.trim().toLowerCase();
      return v === l.secureValue.trim().toLowerCase();
    }).length;
    onProgress?.(fixed, configLines.length);
  };

  const handleSubmit = () => {
    setSubmitted(true);
    if (allFixed) onAllFixed?.();
  };

  const toggleHint = (key: string) => {
    setShowHints((h) => ({ ...h, [key]: !h[key] }));
  };

  return (
    <div
      className={cx(
        "overflow-hidden rounded-2xl border border-border bg-[#0a0c14] shadow-xl",
        className,
      )}
    >
      {/* header */}
      <div className="flex items-center justify-between border-b border-border/60 bg-surface/80 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Icon name="server" size={14} className="text-warning" />
          <span className="font-mono text-[11px] text-muted-foreground">{filename}</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-mono text-[10px]">
            <span className={fixedCount === configLines.length ? "text-success" : "text-warning"}>
              {fixedCount}/{configLines.length} fixed
            </span>
            <span className="text-subtle">({pct}%)</span>
          </div>
          <button
            onClick={handleSubmit}
            className="inline-flex items-center gap-1.5 rounded-lg bg-success/20 px-3 py-1.5 font-mono text-[11px] font-semibold uppercase tracking-wider text-success hover:bg-success/30 active:scale-95 transition-all"
          >
            <Icon name="check-circle" size={12} /> Deploy
          </button>
        </div>
      </div>

      {/* progress bar */}
      <div className="h-1 bg-muted/30">
        <div
          className="h-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            background: allFixed
              ? "var(--color-success)"
              : "linear-gradient(90deg, var(--color-warning), var(--color-cyan))",
          }}
        />
      </div>

      {/* config lines */}
      <div className="max-h-[450px] overflow-auto p-3 no-scrollbar sm:p-4">
        <div className="space-y-2.5">
          {configLines.map((line) => {
            const fixed = isFixed(line);
            const wrong = submitted && !fixed;
            return (
              <div
                key={line.key}
                className={cx(
                  "rounded-xl border p-3 transition-all",
                  fixed
                    ? "border-success/30 bg-success/5"
                    : wrong
                      ? "border-danger/40 bg-danger/5"
                      : "border-border bg-card/50",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Icon
                      name={fixed ? "check-circle" : "alert"}
                      size={14}
                      className={fixed ? "text-success" : "text-danger"}
                    />
                    <span className="font-mono text-xs font-semibold text-foreground">
                      {line.key}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={cx(
                        "rounded-full border px-2 py-0.5 font-mono text-[9px] uppercase tracking-wider",
                        SEV_BADGE[line.severity],
                      )}
                    >
                      {line.severity}
                    </span>
                    <button
                      onClick={() => toggleHint(line.key)}
                      className="rounded-md p-1 text-subtle hover:text-cyan hover:bg-cyan/10"
                      aria-label="Toggle hint"
                    >
                      <Icon name="lightbulb" size={13} />
                    </button>
                  </div>
                </div>

                <div className="mt-2 flex items-center gap-1">
                  <span className="shrink-0 font-mono text-[10px] text-subtle">=</span>
                  <input
                    value={values[line.key]}
                    onChange={(e) => handleChange(line.key, e.target.value)}
                    className={cx(
                      "w-full rounded-md border bg-background/60 px-2.5 py-1.5 font-mono text-xs text-foreground outline-none transition-colors focus:border-cyan/50",
                      fixed ? "border-success/30" : wrong ? "border-danger/30" : "border-border",
                    )}
                    spellCheck={false}
                  />
                </div>

                {showHints[line.key] && (
                  <div className="mt-2 rounded-lg bg-cyan/5 px-3 py-2 font-mono text-[11px] text-cyan/80">
                    💡 {line.hint}
                  </div>
                )}

                {wrong && (
                  <div className="mt-1.5 font-mono text-[10px] text-danger/80">
                    ✗ This value is still insecure
                  </div>
                )}
                {fixed && (
                  <div className="mt-1.5 font-mono text-[10px] text-success/80">
                    ✓ Secure value applied
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
