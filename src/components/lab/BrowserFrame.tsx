import { useState } from "react";
import type { ReactNode } from "react";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

interface BrowserFrameProps {
  url: string;
  title?: string;
  editableUrl?: boolean;
  onNavigate?: (url: string) => void;
  secure?: boolean;
  children: ReactNode;
}

/** A convincing—but clearly labelled—simulated browser chrome. */
export function BrowserFrame({
  url,
  title = "Simulated App",
  editableUrl = false,
  onNavigate,
  secure = true,
  children,
}: BrowserFrameProps) {
  const [draft, setDraft] = useState(url);

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-background shadow-2xl">
      {/* tab strip */}
      <div className="flex items-center gap-1 border-b border-border bg-surface px-2 pt-2 sm:px-3">
        <div className="flex items-center gap-2 rounded-t-lg border-x border-t border-border bg-background px-2 py-1.5 text-xs text-foreground sm:px-3 sm:py-2">
          <Icon name="globe" size={13} className="text-cyan" />
          <span className="max-w-[120px] truncate sm:max-w-[160px]">{title}</span>
        </div>
        <div className="ml-auto hidden items-center gap-1.5 rounded-md bg-warning/10 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-warning sm:inline-flex">
          <Icon name="alert" size={11} /> Simulated Environment
        </div>
      </div>

      {/* toolbar */}
      <div className="flex items-center gap-1.5 border-b border-border bg-surface/60 px-2 py-2 sm:gap-2 sm:px-3 sm:py-2.5">
        <div className="hidden items-center gap-1 text-subtle sm:flex">
          <button className="grid h-7 w-7 place-items-center rounded-md hover:bg-muted" aria-label="Back">
            <Icon name="chevron-right" size={16} className="rotate-180" />
          </button>
          <button className="grid h-7 w-7 place-items-center rounded-md hover:bg-muted" aria-label="Forward">
            <Icon name="chevron-right" size={16} />
          </button>
        </div>
        <form
          className="flex flex-1 items-center gap-2 rounded-lg border border-border bg-background px-3 py-1.5"
          onSubmit={(e) => {
            e.preventDefault();
            onNavigate?.(draft);
          }}
        >
          <span className="relative grid place-items-center">
            {secure && (
              <span
                className="absolute inline-flex h-3 w-3 rounded-full bg-success/40"
                style={{ animation: "pulse-ring 2s infinite" }}
              />
            )}
            <Icon name={secure ? "lock" : "alert"} size={13} className={secure ? "relative text-success" : "text-danger"} />
          </span>
          {editableUrl ? (
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              spellCheck={false}
              className="w-full bg-transparent font-mono text-xs text-foreground outline-none"
              aria-label="Address bar"
            />
          ) : (
            <span className="truncate font-mono text-xs text-muted-foreground">{url}</span>
          )}
          {editableUrl && (
            <button
              type="submit"
              className="rounded-md px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-cyan hover:bg-cyan/10"
            >
              Go
            </button>
          )}
        </form>
      </div>

      {/* viewport */}
      <div className={cx("relative min-h-[220px] overflow-auto bg-white/[0.02] p-4 sm:min-h-[280px] sm:p-6")}>
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-16 opacity-40"
          style={{
            background: "linear-gradient(to bottom, rgba(34,211,238,0.08), transparent)",
            animation: "scan 6s linear infinite",
          }}
        />
        <div className="relative">{children}</div>
      </div>
    </div>
  );
}
