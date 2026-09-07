import { useState } from "react";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

interface CodeEditorProps {
  /** Initial code/content in the editor. */
  initialCode?: string;
  /** Language label shown in the header. */
  language?: string;
  /** Placeholder text when empty. */
  placeholder?: string;
  /** Called when user submits/runs the code. */
  onRun?: (code: string) => void;
  /** Called on every change. */
  onChange?: (code: string) => void;
  /** Button label for the run action. */
  runLabel?: string;
  /** If true, editor is read-only. */
  readOnly?: boolean;
  /** Height constraint. */
  maxHeight?: string;
  className?: string;
}

/** Lightweight code editor with line numbers and run button. */
export function CodeEditor({
  initialCode = "",
  language = "text",
  placeholder = "Type your code here...",
  onRun,
  onChange,
  runLabel = "Run",
  readOnly = false,
  maxHeight = "300px",
  className,
}: CodeEditorProps) {
  const [code, setCode] = useState(initialCode);
  const lines = code.split("\n");

  const handleChange = (val: string) => {
    setCode(val);
    onChange?.(val);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const newVal = code.substring(0, start) + "  " + code.substring(end);
      handleChange(newVal);
      requestAnimationFrame(() => {
        target.selectionStart = target.selectionEnd = start + 2;
      });
    }
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      onRun?.(code);
    }
  };

  return (
    <div
      className={cx(
        "overflow-hidden rounded-2xl border border-border bg-[#0a0c14] shadow-xl",
        className,
      )}
    >
      {/* header */}
      <div className="flex items-center justify-between border-b border-border/60 bg-surface/80 px-4 py-2">
        <div className="flex items-center gap-2">
          <Icon name="code" size={14} className="text-violet" />
          <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
            {language}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {!readOnly && (
            <span className="font-mono text-[9px] text-subtle">Ctrl+Enter to run</span>
          )}
          {onRun && (
            <button
              onClick={() => onRun(code)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary/20 px-3 py-1.5 font-mono text-[11px] font-semibold uppercase tracking-wider text-primary hover:bg-primary/30 active:scale-95 transition-all"
            >
              <Icon name="zap" size={12} /> {runLabel}
            </button>
          )}
        </div>
      </div>

      {/* editor body */}
      <div className="relative flex overflow-auto" style={{ maxHeight }}>
        {/* line numbers */}
        <div className="shrink-0 select-none border-r border-border/30 bg-surface/30 px-3 py-3 font-mono text-[11px] leading-[1.7] text-subtle">
          {lines.map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>

        {/* textarea */}
        <textarea
          value={code}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          readOnly={readOnly}
          spellCheck={false}
          className={cx(
            "flex-1 resize-none bg-transparent p-3 font-mono text-xs leading-[1.7] text-foreground/90 outline-none caret-cyan placeholder:text-subtle",
            readOnly && "cursor-default opacity-70",
          )}
          aria-label="Code editor"
        />
      </div>
    </div>
  );
}
