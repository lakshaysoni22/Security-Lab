import { useEffect, useRef, useState } from "react";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

export interface TerminalCommand {
  /** The command pattern to match (supports simple prefix matching). */
  cmd: string;
  /** The simulated response — can be multi-line string. */
  response: string;
  /** If set, this tag is fired on interaction (used for step progression). */
  tag?: string;
  /** Optional delay in ms before showing response (simulates network). */
  delay?: number;
  /** If true, this response reveals the CTF flag. */
  revealsFlag?: boolean;
}

interface TerminalProps {
  /** Prompt prefix shown before user input. */
  prompt?: string;
  /** Welcome/banner message shown at the top. */
  banner?: string;
  /** Available commands and their responses. */
  commands: TerminalCommand[];
  /** Built-in help text (auto-generated from commands if not provided). */
  helpText?: string;
  /** Callback when a command is executed. */
  onCommand?: (cmd: string, tag?: string) => void;
  /** Callback when CTF flag is revealed. */
  onFlagReveal?: () => void;
  className?: string;
}

interface Line {
  type: "input" | "output" | "error" | "system";
  text: string;
}

const BUILTIN_CMDS = ["help", "clear", "history"];

export function TerminalEmulator({
  prompt = "analyst@trinetlayer",
  banner,
  commands,
  helpText,
  onCommand,
  onFlagReveal,
  className,
}: TerminalProps) {
  const [lines, setLines] = useState<Line[]>(() => {
    const initial: Line[] = [];
    if (banner) {
      initial.push({ type: "system", text: banner });
      initial.push({ type: "system", text: "" });
    }
    return initial;
  });
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [histIdx, setHistIdx] = useState(-1);
  const [processing, setProcessing] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  const focusInput = () => inputRef.current?.focus();

  const addLines = (newLines: Line[]) => {
    setLines((prev) => [...prev, ...newLines]);
  };

  const matchCommand = (raw: string): TerminalCommand | undefined => {
    const trimmed = raw.trim().toLowerCase();
    // Exact match first
    const exact = commands.find((c) => trimmed === c.cmd.toLowerCase());
    if (exact) return exact;
    // Prefix match — check if the user's input starts with a command pattern
    return commands.find((c) => {
      const pattern = c.cmd.toLowerCase();
      return trimmed.startsWith(pattern) || pattern.startsWith(trimmed);
    });
  };

  const processCommand = async (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed) return;

    setHistory((h) => [...h, trimmed]);
    setHistIdx(-1);
    addLines([{ type: "input", text: `${prompt}:~$ ${trimmed}` }]);

    // Built-in commands
    if (trimmed.toLowerCase() === "clear") {
      setLines([]);
      return;
    }
    if (trimmed.toLowerCase() === "history") {
      addLines(history.map((h, i) => ({ type: "output" as const, text: `  ${i + 1}  ${h}` })));
      return;
    }
    if (trimmed.toLowerCase() === "help") {
      const help = helpText ?? generateHelp();
      addLines(help.split("\n").map((l) => ({ type: "output" as const, text: l })));
      return;
    }

    // Match against registered commands
    const match = matchCommand(trimmed);
    if (match) {
      setProcessing(true);
      const delay = match.delay ?? 200 + Math.random() * 300;
      await new Promise((r) => setTimeout(r, delay));
      setProcessing(false);

      const responseLines = match.response.split("\n").map((l) => ({
        type: "output" as const,
        text: l,
      }));
      addLines(responseLines);

      onCommand?.(trimmed, match.tag);
      if (match.revealsFlag) onFlagReveal?.();
    } else {
      addLines([
        { type: "error", text: `bash: ${trimmed.split(" ")[0]}: command not found` },
        { type: "system", text: "Type 'help' for available commands." },
      ]);
    }
  };

  const generateHelp = (): string => {
    const cmdList = [...new Set(commands.map((c) => c.cmd.split(" ")[0]))];
    return [
      "Available commands:",
      "",
      ...cmdList.map((c) => `  ${c}`),
      "",
      "Built-in:",
      "  help     — Show this help",
      "  clear    — Clear terminal",
      "  history  — Show command history",
      "",
      "Tip: Try the commands listed above to investigate the target.",
    ].join("\n");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !processing) {
      e.preventDefault();
      processCommand(input);
      setInput("");
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (history.length === 0) return;
      const newIdx = histIdx < 0 ? history.length - 1 : Math.max(0, histIdx - 1);
      setHistIdx(newIdx);
      setInput(history[newIdx]);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (histIdx < 0) return;
      const newIdx = histIdx + 1;
      if (newIdx >= history.length) {
        setHistIdx(-1);
        setInput("");
      } else {
        setHistIdx(newIdx);
        setInput(history[newIdx]);
      }
    } else if (e.key === "Tab") {
      e.preventDefault();
      // Simple auto-complete
      const trimmed = input.trim().toLowerCase();
      if (!trimmed) return;
      const allCmds = [...commands.map((c) => c.cmd), ...BUILTIN_CMDS];
      const match = allCmds.find((c) => c.toLowerCase().startsWith(trimmed));
      if (match) setInput(match);
    }
  };

  const lineColor = (type: Line["type"]) => {
    switch (type) {
      case "input":
        return "text-cyan";
      case "error":
        return "text-danger";
      case "system":
        return "text-subtle";
      default:
        return "text-foreground/90";
    }
  };

  return (
    <div
      className={cx(
        "overflow-hidden rounded-2xl border border-border bg-[#0a0c14] shadow-2xl",
        className,
      )}
      onClick={focusInput}
    >
      {/* title bar */}
      <div className="flex items-center gap-2 border-b border-border/60 bg-surface/80 px-4 py-2.5">
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full bg-danger/70" />
          <span className="h-3 w-3 rounded-full bg-warning/70" />
          <span className="h-3 w-3 rounded-full bg-success/70" />
        </div>
        <span className="ml-2 flex-1 font-mono text-[11px] text-muted-foreground">
          {prompt} — bash
        </span>
        <div className="inline-flex items-center gap-1.5 rounded-md bg-cyan/10 px-2 py-0.5 font-mono text-[9px] uppercase tracking-wider text-cyan">
          <Icon name="shield" size={10} /> Simulated
        </div>
      </div>

      {/* terminal body */}
      <div className="max-h-[400px] min-h-[250px] overflow-auto p-4 font-mono text-xs leading-relaxed no-scrollbar sm:max-h-[500px]">
        {lines.map((line, i) => (
          <div key={i} className={cx("whitespace-pre-wrap break-all", lineColor(line.type))}>
            {line.text || "\u00A0"}
          </div>
        ))}

        {/* processing indicator */}
        {processing && (
          <div className="flex items-center gap-2 text-subtle">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-cyan" />
            Processing...
          </div>
        )}

        {/* input line */}
        {!processing && (
          <div className="flex items-center gap-0">
            <span className="shrink-0 text-success">{prompt}:~$&nbsp;</span>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 bg-transparent text-foreground outline-none caret-cyan"
              spellCheck={false}
              autoFocus
              aria-label="Terminal input"
            />
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
