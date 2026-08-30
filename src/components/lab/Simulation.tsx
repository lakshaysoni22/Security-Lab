import { useState } from "react";
import type { Lab } from "../../lib/types";
import { BrowserFrame } from "./BrowserFrame";
import { RequestViewer } from "./RequestViewer";
import { TerminalEmulator } from "./TerminalEmulator";
import { CodeEditor } from "./CodeEditor";
import { ConfigEditor as ConfigEditorImported } from "./ConfigEditor";
import { RequestBuilder } from "./RequestBuilder";
import { SandboxPreview } from "./SandboxPreview";
import { CTFFlag } from "./CTFFlag";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

/* eslint-disable @typescript-eslint/no-explicit-any */

type Report = (tag: string) => void;

const SEV_COLOR: Record<string, string> = {
  high: "text-danger",
  medium: "text-warning",
  low: "text-cyan",
  ok: "text-success",
};

/* -------------------------------------------------- Auth (login portal) */
function AuthSim({ sim, report }: { sim: any; report: Report }) {
  const [user, setUser] = useState("");
  const [pw, setPw] = useState("");
  const [msg, setMsg] = useState<{ text: string; exists: boolean } | null>(null);

  const submit = () => {
    if (!user) return;
    const known = (sim.responses as any[]).find((r) => r.user === user);
    if (known) {
      setMsg({ text: known.message, exists: known.exists });
      report(known.exists ? "login:valid" : "login:invalid");
    } else {
      setMsg({ text: `No account found for ${user}.`, exists: false });
      report("login:invalid");
    }
  };

  return (
    <BrowserFrame url={sim.url} title={sim.title}>
      <div className="mx-auto max-w-sm rounded-xl border border-border bg-card p-6">
        <div className="mb-5 text-center">
          <div className="mx-auto mb-2 grid h-11 w-11 place-items-center rounded-lg bg-primary/15 text-cyan">
            <Icon name="lock" size={22} />
          </div>
          <h4 className="font-semibold text-foreground">{sim.title}</h4>
          <p className="text-xs text-muted-foreground">Sign in to continue</p>
        </div>
        <label className="mb-1 block font-mono text-[10px] uppercase tracking-widest text-subtle">
          Username
        </label>
        <input
          value={user}
          onChange={(e) => setUser(e.target.value)}
          placeholder="try: j.doe  or  ghost99"
          className="mb-3 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-cyan/50"
        />
        <label className="mb-1 block font-mono text-[10px] uppercase tracking-widest text-subtle">
          Password
        </label>
        <input
          type="password"
          value={pw}
          onChange={(e) => setPw(e.target.value)}
          placeholder="anything"
          className="mb-4 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-cyan/50"
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button
          onClick={submit}
          className="w-full rounded-lg bg-primary py-2 text-sm font-medium text-primary-foreground hover:brightness-110"
        >
          Sign in
        </button>
        {msg && (
          <div
            className={cx(
              "mt-4 rounded-lg border p-3 text-xs",
              msg.exists
                ? "border-warning/40 bg-warning/5 text-warning"
                : "border-danger/40 bg-danger/5 text-danger",
            )}
          >
            {msg.text}
            <div className="mt-1 font-mono text-[10px] text-muted-foreground">
              server response · notice how it differs by account
            </div>
          </div>
        )}
      </div>
    </BrowserFrame>
  );
}

/* --------------------------------------------- Authz (records / IDOR) */
function AuthzSim({ sim, report }: { sim: any; report: Report }) {
  const you: string = sim.you ?? "1001";
  const records = sim.records as Record<string, { name: string; note: string }>;
  const base = (sim.url as string).split("?")[0];
  const [id, setId] = useState(you);
  const [url, setUrl] = useState(sim.url as string);

  const open = (nextId: string) => {
    setId(nextId);
    setUrl(`${base}?id=${nextId}`);
    report(nextId === you ? "view:1001" : "view:other");
  };
  const onNavigate = (u: string) => {
    const m = u.match(/id=(\d+)/);
    const nextId = m ? m[1] : you;
    open(nextId);
  };
  const rec = records[id];
  const isOwn = id === you;

  return (
    <BrowserFrame url={url} title={sim.title} editableUrl onNavigate={onNavigate}>
      <div className="mx-auto grid max-w-xl gap-3 sm:grid-cols-[150px_1fr]">
        {/* customer list */}
        <div className="rounded-xl border border-border bg-card p-2">
          <div className="px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-subtle">
            Accounts
          </div>
          {Object.keys(records).map((rid) => (
            <button
              key={rid}
              onClick={() => open(rid)}
              className={cx(
                "flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-xs transition-colors hover:bg-muted/40",
                rid === id ? "bg-cyan/10 text-cyan" : "text-muted-foreground",
              )}
            >
              <span className="font-mono">#{rid}</span>
              {rid === you && <span className="text-[9px] uppercase text-success">you</span>}
            </button>
          ))}
        </div>

        {/* record viewer + simulated request inspector */}
        <div className="space-y-3">
          <div className="rounded-lg border border-border bg-surface/60 px-3 py-2 font-mono text-[11px] text-muted-foreground">
            <span className="text-subtle">simulated request →</span>{" "}
            <span className="text-cyan">GET</span> /simulated-record/{id}
          </div>
          {rec ? (
            <div
              className={cx(
                "rounded-xl border p-5",
                isOwn ? "border-border bg-card" : "border-danger/40 bg-danger/5",
              )}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] uppercase tracking-widest text-subtle">
                  Record #{id}
                </span>
                {!isOwn && (
                  <span className="inline-flex items-center gap-1 rounded-md bg-danger/15 px-2 py-0.5 font-mono text-[10px] uppercase text-danger">
                    <Icon name="alert" size={11} /> Not your record
                  </span>
                )}
              </div>
              <h4 className="mt-2 text-lg font-semibold text-foreground">{rec.name}</h4>
              <p className="mt-1 text-sm text-muted-foreground">{rec.note}</p>
              <div className="mt-3 font-mono text-[10px] text-subtle">
                200 OK · returned without an ownership check
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-card p-5 text-sm text-muted-foreground">
              No record found for #{id}.
            </div>
          )}
        </div>
      </div>
    </BrowserFrame>
  );
}

/* ----------------------------------------------- Input (test toolbox) */
interface InputTest {
  id: string;
  label: string;
  field: string;
  input: string;
  result: string;
  observation: string;
  impact: string;
  severity: string;
  reflect?: boolean;
}

function InputToolbox({ sim, report }: { sim: any; report: Report }) {
  const tests = sim.tests as InputTest[];
  const [ran, setRan] = useState<string[]>([]);

  const run = (t: InputTest) => {
    if (ran.includes(t.id)) return;
    const next = [...ran, t.id];
    setRan(next);
    report(`test:${t.id}`);
    if (next.length === tests.length) report("tests:complete");
  };

  const rows = tests.filter((t) => ran.includes(t.id));
  const charsTest = tests.find((t) => t.reflect && ran.includes(t.id));

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-2 rounded-xl border border-violet/30 bg-violet/5 p-3 text-xs text-violet">
        <Icon name="shield" size={14} className="mt-0.5 shrink-0" />
        <span>{sim.note}</span>
      </div>

      <div className="overflow-hidden rounded-2xl border border-border bg-card">
        <div className="flex items-center gap-2 border-b border-border bg-surface px-4 py-2.5">
          <Icon name="code" size={15} className="text-violet" />
          <span className="font-mono text-xs text-muted-foreground">{sim.app} · test toolbox</span>
          <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-subtle">
            {ran.length}/{tests.length} run
          </span>
        </div>

        {/* test buttons */}
        <div className="flex flex-wrap gap-2 border-b border-border p-3">
          {tests.map((t) => (
            <button
              key={t.id}
              onClick={() => run(t)}
              disabled={ran.includes(t.id)}
              className={cx(
                "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 font-mono text-[11px] transition-colors",
                ran.includes(t.id)
                  ? "border-border bg-muted/40 text-subtle"
                  : "border-violet/40 text-violet hover:bg-violet/5",
              )}
            >
              {ran.includes(t.id) ? <Icon name="check" size={12} /> : <Icon name="play" size={12} />}
              {t.label}
            </button>
          ))}
        </div>

        {/* results table */}
        {rows.length === 0 ? (
          <p className="p-5 text-center text-xs text-subtle">
            Run a test to record its result, observation and security impact.
          </p>
        ) : (
          <div className="divide-y divide-border/60">
            {rows.map((t) => (
              <div key={t.id} className="grid gap-1 px-4 py-3 sm:grid-cols-[130px_1fr]">
                <div>
                  <div className="text-sm font-medium text-foreground">{t.label}</div>
                  <div className="font-mono text-[10px] text-subtle">
                    {t.field}: {t.input === "" ? "(empty)" : t.input}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={cx(
                        "rounded px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider",
                        t.result === "reflected"
                          ? "bg-danger/15 text-danger"
                          : "bg-muted text-muted-foreground",
                      )}
                    >
                      {t.result}
                    </span>
                    <span className={cx("font-mono text-[10px] uppercase", SEV_COLOR[t.severity])}>
                      {t.severity === "ok" ? "no issue" : `${t.severity} impact`}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{t.observation}</p>
                  <p className="text-xs text-subtle">Impact: {t.impact}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* contained reflected-render demo (predefined payload only) */}
      {charsTest && (
        <div className="rounded-2xl border border-danger/40 bg-danger/5 p-4">
          <div className="mb-2 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-danger">
            <Icon name="alert" size={12} /> Reflected output (contained demo)
          </div>
          <div className="rounded-lg border border-border bg-background p-3 text-sm text-foreground">
            {/* Predefined payload rendered as HTML to demonstrate the flaw — never user-supplied. */}
            <div dangerouslySetInnerHTML={{ __html: charsTest.input }} />
          </div>
          <p className="mt-2 text-xs text-danger">
            The portal rendered the predefined markup as live HTML instead of text — that is
            reflected XSS.
          </p>
        </div>
      )}
    </div>
  );
}

/* ----------------------------------------- Config (security review) */
interface ConfigLine {
  key: string;
  value: string;
  section: string;
  severity: string;
  reason: string;
  secure: string;
}

function ConfigSim({ sim, report }: { sim: any; report: Report }) {
  const lines = sim.lines as ConfigLine[];
  const [flagged, setFlagged] = useState<Set<string>>(new Set());
  const [showSecure, setShowSecure] = useState(false);

  const toggleFlag = (key: string) => {
    setFlagged((s) => {
      const n = new Set(s);
      n.has(key) ? n.delete(key) : n.add(key);
      if (n.size >= 3) report("flag:3");
      return n;
    });
  };
  const toggleSecure = () => {
    setShowSecure((v) => {
      if (!v) report("diff:viewed");
      return !v;
    });
  };

  const sections = Array.from(new Set(lines.map((l) => l.section)));

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-background">
      <div className="flex flex-wrap items-center gap-2 border-b border-border bg-surface px-4 py-2.5">
        <Icon name="server" size={15} className="text-warning" />
        <span className="font-mono text-xs text-muted-foreground">{sim.filename}</span>
        <button
          onClick={toggleSecure}
          className={cx(
            "ml-auto rounded-md border px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider transition-colors",
            showSecure
              ? "border-success/40 bg-success/10 text-success"
              : "border-border text-muted-foreground hover:text-foreground",
          )}
        >
          {showSecure ? "Showing hardened baseline" : "Compare secure baseline"}
        </button>
      </div>

      <div className="divide-y divide-border/60">
        {sections.map((section) => (
          <div key={section} className="px-4 py-3">
            <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-subtle">
              {section}
            </div>
            <div className="space-y-1.5">
              {lines
                .filter((l) => l.section === section)
                .map((ln) => {
                  const on = flagged.has(ln.key);
                  return (
                    <button
                      key={ln.key}
                      onClick={() => toggleFlag(ln.key)}
                      className={cx(
                        "w-full rounded-lg border px-3 py-2 text-left transition-colors",
                        on ? "border-warning/50 bg-warning/5" : "border-border hover:bg-muted/30",
                      )}
                    >
                      <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
                        <span className="text-cyan">{ln.key}</span>
                        <span className="text-subtle">=</span>
                        <span className={cx(showSecure && ln.value !== ln.secure && "text-danger line-through")}>
                          {ln.value}
                        </span>
                        {showSecure && ln.value !== ln.secure && (
                          <>
                            <Icon name="arrow-right" size={12} className="text-success" />
                            <span className="text-success">{ln.secure}</span>
                          </>
                        )}
                        <span
                          className={cx(
                            "ml-auto flex items-center gap-1 text-[10px] uppercase",
                            SEV_COLOR[ln.severity],
                          )}
                        >
                          {ln.severity !== "ok" && <Icon name="alert" size={11} />}
                          {ln.severity === "ok" ? "ok" : ln.severity}
                        </span>
                        {on && <Icon name="check" size={13} className="text-warning" />}
                      </div>
                      <p className="mt-1 text-[11px] text-muted-foreground">{ln.reason}</p>
                    </button>
                  );
                })}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-border bg-surface/50 px-4 py-2.5 font-mono text-[11px] text-muted-foreground">
        {flagged.size} line(s) flagged — reserve High severity for the worst offenders.
      </div>
    </div>
  );
}

export function Simulation({
  lab,
  onInteraction,
}: {
  lab: Lab;
  onInteraction?: Report;
}) {
  const [mode, setMode] = useState<"guided" | "practical">("guided");
  const [flagRevealed, setFlagRevealed] = useState(false);
  const sim = lab.sim as any;
  const report: Report = (tag) => onInteraction?.(tag);

  const guidedContent = (() => {
    if (lab.simulation === "request") {
      return (
        <RequestViewer request={sim.request} response={sim.response} onInteraction={report} />
      );
    }
    if (lab.simulation === "form") return <InputToolbox sim={sim} report={report} />;
    if (lab.simulation === "config") return <ConfigSim sim={sim} report={report} />;
    if (lab.id === "authz") return <AuthzSim sim={sim} report={report} />;
    return <AuthSim sim={sim} report={report} />;
  })();

  const practicalContent = (() => {
    switch (lab.id) {
      case "auth":
        return <AuthPractical report={report} onFlagReveal={() => setFlagRevealed(true)} flagRevealed={flagRevealed} />;
      case "authz":
        return <AuthzPractical report={report} onFlagReveal={() => setFlagRevealed(true)} flagRevealed={flagRevealed} />;
      case "input":
        return <InputPractical report={report} onFlagReveal={() => setFlagRevealed(true)} flagRevealed={flagRevealed} />;
      case "config":
        return <ConfigPractical report={report} onFlagReveal={() => setFlagRevealed(true)} flagRevealed={flagRevealed} />;
      case "http":
        return <HttpPractical report={report} onFlagReveal={() => setFlagRevealed(true)} flagRevealed={flagRevealed} />;
      default:
        return guidedContent;
    }
  })();

  return (
    <div className="space-y-4">
      {/* Mode toggle */}
      <div className="flex items-center gap-1 rounded-xl border border-border bg-card p-1">
        <button
          onClick={() => setMode("guided")}
          className={cx(
            "flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 font-mono text-xs font-semibold uppercase tracking-wider transition-all",
            mode === "guided"
              ? "bg-primary/15 text-primary shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          <Icon name="compass" size={14} /> Guided
          <span className="hidden text-[9px] font-normal normal-case tracking-normal text-muted-foreground sm:inline">
            (35%)
          </span>
        </button>
        <button
          onClick={() => setMode("practical")}
          className={cx(
            "flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 font-mono text-xs font-semibold uppercase tracking-wider transition-all",
            mode === "practical"
              ? "bg-cyan/15 text-cyan shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          <Icon name="terminal" size={14} /> Practical
          <span className="hidden text-[9px] font-normal normal-case tracking-normal text-muted-foreground sm:inline">
            (65%)
          </span>
        </button>
      </div>

      {/* Content */}
      <div key={mode} className="animate-fade-slide">
        {mode === "guided" ? guidedContent : practicalContent}
      </div>
    </div>
  );
}

/* ======================================================================
   PRACTICAL MODE COMPONENTS — one per lab, 65% of the content
   ====================================================================== */

/* ----- Lab 01: Auth Enumeration Practical ----- */
function AuthPractical({ report, onFlagReveal, flagRevealed }: { report: Report; onFlagReveal: () => void; flagRevealed: boolean }) {
  const [enumCount, setEnumCount] = useState(0);
  const [fixCode, setFixCode] = useState("");
  const [fixResult, setFixResult] = useState<"none" | "wrong" | "correct">("none");

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-cyan/20 bg-cyan/5 px-4 py-3">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-cyan">
          <Icon name="terminal" size={13} /> Practical Challenge: Enumerate the Portal
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Use the terminal below to probe the login API with <code className="rounded bg-muted px-1 text-xs text-cyan">curl</code> commands.
          Enumerate at least <strong className="text-foreground">3 valid users</strong> to capture the flag. The API responds differently
          for existing vs non-existing accounts — that is the vulnerability.
        </p>
      </div>

      <TerminalEmulator
        prompt="analyst@cyberlabs"
        banner={[
          "╔══════════════════════════════════════════════════════════╗",
          "║  CYBER LABS — Lab 01: Auth Enumeration                   ║",
          "║  Target: https://portal.northstar-systems.internal     ║",
          "║  Objective: Enumerate valid user accounts               ║",
          "╚══════════════════════════════════════════════════════════╝",
          "",
          "Type 'help' for available commands.",
        ].join("\n")}
        commands={[
          { cmd: "curl -X POST https://portal.northstar-systems.internal/login -d \"user=j.doe&pass=test\"", response: "HTTP/1.1 401 Unauthorized\nContent-Type: application/json\n\n{\"error\": \"Wrong password for j.doe.\", \"code\": \"INVALID_PASSWORD\"}\n\n[!] Notice: The server confirms user 'j.doe' EXISTS.", tag: "login:valid", delay: 400 },
          { cmd: "curl -X POST https://portal.northstar-systems.internal/login -d \"user=ghost99&pass=test\"", response: "HTTP/1.1 401 Unauthorized\nContent-Type: application/json\n\n{\"error\": \"No account found for ghost99.\", \"code\": \"USER_NOT_FOUND\"}\n\n[i] Notice: Different error = user does NOT exist.", tag: "login:invalid", delay: 350 },
          { cmd: "curl -X POST https://portal.northstar-systems.internal/login -d \"user=admin&pass=test\"", response: "HTTP/1.1 401 Unauthorized\nContent-Type: application/json\n\n{\"error\": \"Wrong password for admin.\", \"code\": \"INVALID_PASSWORD\"}\n\n[!] User 'admin' EXISTS — high-value target identified.", tag: "login:valid", delay: 380 },
          { cmd: "curl -X POST https://portal.northstar-systems.internal/login -d \"user=s.kumar&pass=test\"", response: "HTTP/1.1 401 Unauthorized\nContent-Type: application/json\n\n{\"error\": \"Wrong password for s.kumar.\", \"code\": \"INVALID_PASSWORD\"}\n\n[!] User 's.kumar' EXISTS.", tag: "login:valid", delay: 360 },
          { cmd: "curl -X POST https://portal.northstar-systems.internal/login -d \"user=test&pass=test\"", response: "HTTP/1.1 401 Unauthorized\nContent-Type: application/json\n\n{\"error\": \"No account found for test.\", \"code\": \"USER_NOT_FOUND\"}", tag: "login:invalid", delay: 300 },
          { cmd: "curl -X POST https://portal.northstar-systems.internal/login -d \"user=r.chen&pass=test\"", response: "HTTP/1.1 401 Unauthorized\nContent-Type: application/json\nX-Debug-Flag: FLAG{enum_is_the_first_step}\n\n{\"error\": \"Wrong password for r.chen.\", \"code\": \"INVALID_PASSWORD\"}\n\n[!] User 'r.chen' EXISTS.\n[★] FLAG FOUND in response header: FLAG{enum_is_the_first_step}", tag: "login:valid", revealsFlag: true, delay: 500 },
          { cmd: "nmap -sV portal.northstar-systems.internal", response: "Starting Nmap 7.94 ( https://nmap.org )\nPORT    STATE  SERVICE  VERSION\n22/tcp  closed ssh\n80/tcp  open   http     nginx 1.24.0\n443/tcp open   https    nginx 1.24.0\n3306/tcp closed mysql\n\n[i] Only HTTP/HTTPS ports open. Focus on the web login API.", delay: 800 },
          { cmd: "ls", response: "notes.txt  wordlist.txt  recon.sh", delay: 100 },
          { cmd: "cat notes.txt", response: "=== Recon Notes ===\n- Target has a login endpoint at /login\n- POST body expects: user=<username>&pass=<password>\n- The error messages differ based on whether the user exists\n- This is a classic username enumeration vulnerability\n- Enumerate users, then build a targeted wordlist", delay: 200 },
          { cmd: "cat wordlist.txt", response: "j.doe\nadmin\ns.kumar\nr.chen\nghost99\ntest\nroot\nservice-account\nbackup-admin", delay: 150 },
        ]}
        onCommand={(cmd, tag) => {
          if (tag === "login:valid") {
            setEnumCount((c) => c + 1);
            report(tag);
          }
          if (tag === "login:invalid") report(tag);
        }}
        onFlagReveal={onFlagReveal}
      />

      <CTFFlag flag="FLAG{enum_is_the_first_step}" revealed={flagRevealed} />

      {/* Fix challenge */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-violet">
          <Icon name="code" size={13} /> Fix Challenge: Write the Secure Error Message
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          The vulnerability exists because the server gives <strong className="text-foreground">different error messages</strong> for
          valid vs invalid users. Write a single, generic error message that should be used for ALL failed logins:
        </p>
        <div className="mt-3">
          <CodeEditor
            initialCode=""
            language="json"
            placeholder='{"error": "Your secure error message here"}'
            runLabel="Validate Fix"
            onRun={(code) => {
              const lower = code.toLowerCase();
              const isGeneric =
                !lower.includes("wrong password") &&
                !lower.includes("no account") &&
                !lower.includes("not found") &&
                !lower.includes("user exists") &&
                (lower.includes("invalid") || lower.includes("incorrect") || lower.includes("failed"));
              setFixResult(isGeneric ? "correct" : "wrong");
              if (isGeneric) report("fix:auth");
            }}
          />
        </div>
        {fixResult === "correct" && (
          <div className="mt-2 rounded-lg bg-success/10 px-3 py-2 font-mono text-xs text-success">
            ✓ Correct! A generic message like this prevents username enumeration.
          </div>
        )}
        {fixResult === "wrong" && (
          <div className="mt-2 rounded-lg bg-danger/10 px-3 py-2 font-mono text-xs text-danger">
            ✗ This message still leaks information. Make it identical for both valid and invalid users.
          </div>
        )}
      </div>
    </div>
  );
}

/* ----- Lab 02: IDOR Practical ----- */
function AuthzPractical({ report, onFlagReveal, flagRevealed }: { report: Report; onFlagReveal: () => void; flagRevealed: boolean }) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-cyan/20 bg-cyan/5 px-4 py-3">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-cyan">
          <Icon name="terminal" size={13} /> Practical Challenge: Exploit the IDOR
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          You are logged in as <code className="rounded bg-muted px-1 text-xs text-cyan">user #1001</code>. Use the Request Builder
          to access records belonging to other users. The API does <strong className="text-foreground">no authorization check</strong> — any authenticated
          user can access any record by changing the ID. Find the flag hidden in record <code className="rounded bg-muted px-1 text-xs text-warning">#1003</code>.
        </p>
      </div>

      <RequestBuilder
        baseUrl="https://api.northstar.internal"
        endpoints={[
          {
            method: "GET", path: "/records/1001",
            response: { status: 200, statusText: "OK", headers: { "Content-Type": "application/json", "X-User-Context": "1001" }, body: JSON.stringify({ id: 1001, name: "Your Support Ticket", customer: "You (User #1001)", issue: "Password reset request", status: "Open", notes: "Normal access — this is your own record." }, null, 2) },
            tag: "idor:own",
          },
          {
            method: "GET", path: "/records/1002",
            response: { status: 200, statusText: "OK", headers: { "Content-Type": "application/json", "X-User-Context": "1001", "X-Warning": "Cross-account access detected" }, body: JSON.stringify({ id: 1002, name: "Alice's Billing Dispute", customer: "Alice (User #1002)", issue: "Charged twice for subscription", status: "Resolved", notes: "CONFIDENTIAL: Refund of $249 processed to card ending 4829.", internal_note: "⚠ You should NOT be seeing this record. This is an IDOR vulnerability." }, null, 2) },
            tag: "idor:other",
          },
          {
            method: "GET", path: "/records/1003",
            response: { status: 200, statusText: "OK", headers: { "Content-Type": "application/json", "X-User-Context": "1001", "X-CTF-Flag": "FLAG{idor_no_authz_check}" }, body: JSON.stringify({ id: 1003, name: "Bob's Account Deletion", customer: "Bob (User #1003)", issue: "Request to delete account and all data", status: "Pending Review", notes: "CRITICAL: Contains PII — SSN ending 4721, DOB 1985-03-14", flag: "FLAG{idor_no_authz_check}", internal_note: "🏁 FLAG CAPTURED! The server blindly trusted the record ID without checking authorization." }, null, 2) },
            tag: "idor:flag", revealsFlag: true,
          },
          {
            method: "GET", path: "/records/1004",
            response: { status: 200, statusText: "OK", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: 1004, name: "Charlie's VPN Access", customer: "Charlie (User #1004)", issue: "VPN credentials not working", status: "In Progress", notes: "Sent new credentials via internal chat. Username: c.martinez, Temp password: Northstar2024!" }, null, 2) },
            tag: "idor:other",
          },
          {
            method: "DELETE", path: "/records/1003",
            response: { status: 403, statusText: "Forbidden", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ error: "DELETE not allowed in demo mode. Nice try though! 😄" }, null, 2) },
          },
        ]}
        onRequest={(method, path, tag) => {
          if (tag) report(tag);
        }}
        onFlagReveal={onFlagReveal}
      />

      <CTFFlag flag="FLAG{idor_no_authz_check}" revealed={flagRevealed} label="IDOR Exploited!" />

      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-violet">
          <Icon name="shield" size={13} /> Defender Question
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          The server checks <strong className="text-foreground">who you are</strong> (authentication via cookie) but never checks
          <strong className="text-foreground"> what you can access</strong> (authorization). What single check would fix this?
          The server should compare the <code className="rounded bg-muted px-1 text-xs">session.userId</code> against the
          <code className="rounded bg-muted px-1 text-xs">record.ownerId</code> before returning data.
        </p>
      </div>
    </div>
  );
}

/* ----- Lab 03: Input Validation / XSS Practical ----- */
function InputPractical({ report, onFlagReveal, flagRevealed }: { report: Report; onFlagReveal: () => void; flagRevealed: boolean }) {
  const [payload, setPayload] = useState("");
  const [submitted, setSubmitted] = useState(false);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-cyan/20 bg-cyan/5 px-4 py-3">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-cyan">
          <Icon name="code" size={13} /> Practical Challenge: Craft an XSS Payload
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          The search form below reflects your input directly into the page <strong className="text-foreground">without sanitization</strong>.
          Write an XSS payload in the editor and click <strong className="text-foreground">Inject</strong> to execute it.
          Successfully trigger <code className="rounded bg-muted px-1 text-xs text-danger">alert()</code> to capture the flag.
        </p>
      </div>

      <CodeEditor
        initialCode={'<script>alert("XSS")</script>'}
        language="html"
        placeholder="Write your XSS payload here..."
        runLabel="Inject Payload"
        onRun={(code) => {
          setPayload(code);
          setSubmitted(true);
          report("xss:inject");
        }}
      />

      {submitted && (
        <SandboxPreview
          html={payload}
          title="Northstar Search — search.northstar.internal"
          onXSSDetected={() => {
            onFlagReveal();
            report("xss:success");
          }}
        />
      )}

      <CTFFlag flag="FLAG{xss_payload_executed}" revealed={flagRevealed} label="XSS Executed!" />

      {/* Fix challenge */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-violet">
          <Icon name="code" size={13} /> Fix Challenge: Write a Sanitizer
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Now write a JavaScript function that sanitizes user input to prevent XSS. It should escape
          <code className="rounded bg-muted px-1 text-xs">&lt;</code>,
          <code className="rounded bg-muted px-1 text-xs">&gt;</code>,
          <code className="rounded bg-muted px-1 text-xs">&amp;</code>,
          <code className="rounded bg-muted px-1 text-xs">&quot;</code>, and
          <code className="rounded bg-muted px-1 text-xs">&apos;</code>.
        </p>
        <div className="mt-3">
          <CodeEditor
            initialCode={`function sanitize(input) {\n  // Replace dangerous characters with HTML entities\n  \n}`}
            language="javascript"
            runLabel="Test Sanitizer"
            onRun={(code) => {
              const hasReplace = code.includes(".replace") || code.includes("replaceAll");
              const hasEntities = code.includes("&lt;") || code.includes("&amp;") || code.includes("encodeURI") || code.includes("textContent") || code.includes("innerText");
              if (hasReplace || hasEntities) {
                report("fix:xss");
              }
            }}
          />
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-warning">
          <Icon name="zap" size={13} /> Payload Cheat Sheet
        </div>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {[
            { label: "Basic", code: '<script>alert("XSS")</script>' },
            { label: "IMG tag", code: '<img src=x onerror=alert("XSS")>' },
            { label: "SVG", code: '<svg onload=alert("XSS")>' },
            { label: "Event", code: '<div onmouseover=alert("XSS")>Hover me</div>' },
            { label: "Body", code: '<body onload=alert("XSS")>' },
            { label: "Encoded", code: "<img src=x onerror=alert(String.fromCharCode(88,83,83))>" },
          ].map((p) => (
            <button
              key={p.label}
              onClick={() => {
                setPayload(p.code);
                setSubmitted(true);
                report("xss:inject");
              }}
              className="rounded-lg border border-border bg-background/60 px-3 py-2 text-left transition-all hover:border-danger/40 hover:bg-danger/5"
            >
              <div className="font-mono text-[9px] uppercase text-subtle">{p.label}</div>
              <div className="mt-0.5 truncate font-mono text-[11px] text-danger/80">{p.code}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ----- Lab 04: Config Misconfiguration Practical ----- */
function ConfigPractical({ report, onFlagReveal, flagRevealed }: { report: Report; onFlagReveal: () => void; flagRevealed: boolean }) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-cyan/20 bg-cyan/5 px-4 py-3">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-cyan">
          <Icon name="server" size={13} /> Practical Challenge: Harden the Deployment
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          The Northstar Operations Dashboard is shipping with <strong className="text-foreground">factory defaults</strong>.
          Fix every insecure setting below. Click the <strong className="text-foreground">hint icon</strong> (?) next to each line for guidance.
          Fix all 8 settings to deploy securely and capture the flag.
        </p>
      </div>

      <ConfigEditorComponent
        configLines={[
          { key: "NODE_ENV", insecureValue: "development", secureValue: "production", hint: "Production deployments must use 'production' to disable debug features and stack traces.", severity: "critical" },
          { key: "DEBUG", insecureValue: "true", secureValue: "false", hint: "Debug mode exposes internal state, stack traces, and verbose error messages to attackers.", severity: "critical" },
          { key: "ADMIN_PASSWORD", insecureValue: "admin123", secureValue: "use-vault-secret", hint: "Never hardcode passwords. Use a secret manager like HashiCorp Vault or AWS Secrets Manager. Set to 'use-vault-secret'.", severity: "critical" },
          { key: "SESSION_SECRET", insecureValue: "keyboard-cat", secureValue: "use-vault-secret", hint: "A weak session secret allows attackers to forge session cookies. Use a cryptographically random value from a vault.", severity: "critical" },
          { key: "CORS_ORIGIN", insecureValue: "*", secureValue: "https://dashboard.northstar.internal", hint: "Wildcard CORS allows any website to make authenticated requests. Restrict to your specific origin.", severity: "high" },
          { key: "RATE_LIMIT_ENABLED", insecureValue: "false", secureValue: "true", hint: "Without rate limiting, attackers can brute-force credentials and overwhelm the API.", severity: "high" },
          { key: "LOG_LEVEL", insecureValue: "verbose", secureValue: "warn", hint: "Verbose logging in production can leak sensitive data into log files. Use 'warn' or 'error'.", severity: "medium" },
          { key: "TLS_MIN_VERSION", insecureValue: "TLSv1.0", secureValue: "TLSv1.2", hint: "TLS 1.0 and 1.1 are deprecated and vulnerable to BEAST/POODLE attacks. Minimum should be TLSv1.2.", severity: "high" },
        ]}
        onAllFixed={() => {
          onFlagReveal();
          report("config:all-fixed");
        }}
        onProgress={(fixed, total) => {
          if (fixed > 0) report("config:fix");
        }}
      />

      <CTFFlag flag="FLAG{hardened_config_deployed}" revealed={flagRevealed} label="Config Hardened!" />
    </div>
  );
}

/* Wrapper to avoid naming conflict with the guided ConfigSim */
function ConfigEditorComponent(props: import("./ConfigEditor").ConfigLine extends infer CL ? {
  configLines: CL[];
  onAllFixed?: () => void;
  onProgress?: (fixed: number, total: number) => void;
} : never) {
  return <ConfigEditorImported {...props} />;
}

/* ----- Lab 05: HTTP Security Practical ----- */
function HttpPractical({ report, onFlagReveal, flagRevealed }: { report: Report; onFlagReveal: () => void; flagRevealed: boolean }) {
  const [headerCode, setHeaderCode] = useState("");
  const [headerResult, setHeaderResult] = useState<"none" | "partial" | "correct">("none");

  const requiredHeaders = [
    "strict-transport-security",
    "x-content-type-options",
    "content-security-policy",
    "x-frame-options",
  ];

  const checkHeaders = (code: string) => {
    const lower = code.toLowerCase();
    const found = requiredHeaders.filter((h) => lower.includes(h));
    if (found.length >= 4) {
      setHeaderResult("correct");
      onFlagReveal();
      report("http:headers-fixed");
    } else if (found.length > 0) {
      setHeaderResult("partial");
      report("http:header-added");
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-cyan/20 bg-cyan/5 px-4 py-3">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-cyan">
          <Icon name="activity" size={13} /> Practical Challenge: Secure the Headers
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Use the Request Builder to inspect the API responses. Notice the <strong className="text-foreground">missing security headers</strong>.
          Then write the correct headers in the editor below. You need at least <strong className="text-foreground">4 security headers</strong>.
        </p>
      </div>

      <RequestBuilder
        baseUrl="https://api.atlas-notes.example"
        endpoints={[
          {
            method: "GET", path: "/api/notes",
            response: {
              status: 200, statusText: "OK",
              headers: {
                "Content-Type": "application/json",
                "Server": "nginx/1.24.0",
                "X-Powered-By": "Express",
              },
              body: JSON.stringify({
                notes: [
                  { id: 1, title: "Meeting notes", content: "Q3 roadmap discussion..." },
                  { id: 2, title: "TODO", content: "Fix auth bypass in /admin..." },
                ],
                _warning: "⚠ Notice: No security headers in the response! No HSTS, no CSP, no X-Frame-Options.",
              }, null, 2),
            },
            tag: "http:inspect-response",
          },
          {
            method: "GET", path: "/api/user",
            response: {
              status: 200, statusText: "OK",
              headers: {
                "Content-Type": "application/json",
                "Set-Cookie": "session=abc123; Path=/",
              },
              body: JSON.stringify({
                user: { id: 42, name: "analyst", role: "user" },
                _warning: "⚠ Cookie has no HttpOnly, Secure, or SameSite flags!",
              }, null, 2),
            },
            tag: "http:inspect-cookie",
          },
          {
            method: "GET", path: "/admin",
            response: {
              status: 200, statusText: "OK",
              headers: { "Content-Type": "text/html" },
              body: "<html><body><h1>Admin Panel</h1><p>No authentication required!</p><p>⚠ This page has no X-Frame-Options — it can be embedded in an attacker's iframe (clickjacking).</p></body></html>",
            },
            tag: "http:inspect-admin",
          },
        ]}
        onRequest={(method, path, tag) => {
          if (tag) report(tag);
        }}
      />

      {/* Header editor */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-violet">
          <Icon name="shield" size={13} /> Fix: Add Security Headers
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Write the response headers that should be added. Include at minimum:
          <code className="mx-1 rounded bg-muted px-1 text-xs text-cyan">Strict-Transport-Security</code>,
          <code className="mx-1 rounded bg-muted px-1 text-xs text-cyan">X-Content-Type-Options</code>,
          <code className="mx-1 rounded bg-muted px-1 text-xs text-cyan">Content-Security-Policy</code>, and
          <code className="mx-1 rounded bg-muted px-1 text-xs text-cyan">X-Frame-Options</code>.
        </p>
        <div className="mt-3">
          <CodeEditor
            initialCode={`# Add the missing security headers below:\n\nStrict-Transport-Security: \nX-Content-Type-Options: \nContent-Security-Policy: \nX-Frame-Options: `}
            language="http"
            runLabel="Validate Headers"
            onRun={checkHeaders}
          />
        </div>
        {headerResult === "partial" && (
          <div className="mt-2 rounded-lg bg-warning/10 px-3 py-2 font-mono text-xs text-warning">
            ⚠ Some headers found, but you need all 4 with correct values. Fill in the values!
          </div>
        )}
        {headerResult === "correct" && (
          <div className="mt-2 rounded-lg bg-success/10 px-3 py-2 font-mono text-xs text-success">
            ✓ All 4 security headers present! The response is now hardened against common attacks.
          </div>
        )}
      </div>

      <CTFFlag flag="FLAG{headers_locked_down}" revealed={flagRevealed} label="Headers Secured!" />
    </div>
  );
}

