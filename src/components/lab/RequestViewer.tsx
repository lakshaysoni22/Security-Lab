import { useState } from "react";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

type Side = "request" | "response";
type Tab = "overview" | "headers" | "query" | "body";

interface ReqData {
  method: string;
  path: string;
  host: string;
  headers: Record<string, string>;
  query: Record<string, string>;
}
interface ResData {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  body: unknown;
  missing: string[];
  cookieIssues: string[];
  safeSetCookie?: string;
  safeHeaders?: Record<string, string>;
}

function CopyBtn({ text, onCopied }: { text: string; onCopied?: () => void }) {
  const [done, setDone] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard?.writeText(text).then(
          () => {
            setDone(true);
            onCopied?.();
            setTimeout(() => setDone(false), 1200);
          },
          () => {},
        );
      }}
      className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-subtle hover:bg-muted hover:text-cyan"
    >
      <Icon name={done ? "check" : "copy"} size={12} /> {done ? "Copied" : "Copy"}
    </button>
  );
}

/** Minimal JSON syntax highlighter → coloured spans. */
function JsonHighlight({ value }: { value: unknown }) {
  const json = JSON.stringify(value, null, 2);
  const tokens = json.split(/("(?:\\.|[^"\\])*"(?:\s*:)?|\b(?:true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g);
  return (
    <>
      {tokens.map((t, i) => {
        if (!t) return null;
        let cls = "text-foreground";
        if (/^"/.test(t)) {
          cls = /:\s*$/.test(t) ? "text-cyan" : "text-success";
        } else if (/^(true|false|null)$/.test(t)) {
          cls = "text-violet";
        } else if (/^-?\d/.test(t)) {
          cls = "text-warning";
        }
        return (
          <span key={i} className={cls}>
            {t}
          </span>
        );
      })}
    </>
  );
}

function HeaderRows({
  headers,
  flags,
}: {
  headers: Record<string, string>;
  flags?: Record<string, "warn" | "ok">;
}) {
  return (
    <div className="divide-y divide-border/60 font-mono text-xs">
      {Object.entries(headers).map(([k, v]) => {
        const flag = flags?.[k];
        return (
          <div key={k} className="flex flex-wrap items-start gap-x-2 py-2">
            <span className={cx("shrink-0", flag === "warn" ? "text-warning" : "text-cyan")}>{k}:</span>
            <span className="break-all text-muted-foreground">{v}</span>
            {flag === "warn" && (
              <span className="ml-auto inline-flex items-center gap-1 text-[10px] text-warning">
                <Icon name="alert" size={11} /> review
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function RequestViewer({
  request,
  response,
  onInteraction,
}: {
  request: ReqData;
  response: ResData;
  onInteraction?: (tag: string) => void;
}) {
  const [side, setSide] = useState<Side>("request");
  const [tab, setTab] = useState<Tab>("overview");
  const [toast, setToast] = useState(false);
  const showToast = () => {
    setToast(true);
    setTimeout(() => setToast(false), 1600);
  };

  const isReq = side === "request";
  const tabs: Tab[] = isReq ? ["overview", "headers", "query"] : ["overview", "headers", "body"];

  const setCurrentSide = (s: Side) => {
    setSide(s);
    setTab("overview");
    if (s === "response") onInteraction?.("viewer:explored");
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-background">
      {/* copy toast */}
      <div
        aria-live="polite"
        className={cx(
          "pointer-events-none absolute right-3 top-3 z-20 inline-flex items-center gap-1.5 rounded-lg border border-cyan/30 bg-card/95 px-3 py-1.5 font-mono text-[10px] uppercase tracking-wider text-cyan shadow-lg transition-all duration-300",
          toast ? "translate-y-0 opacity-100" : "-translate-y-2 opacity-0",
        )}
      >
        <Icon name="check" size={12} /> Copied to clipboard
      </div>
      {/* status bar */}
      <div className="flex flex-wrap items-center gap-3 border-b border-border bg-surface px-4 py-3">
        <span className="rounded-md bg-primary/15 px-2 py-1 font-mono text-xs font-semibold text-primary">
          {request.method}
        </span>
        <span className="font-mono text-xs text-muted-foreground">{request.path}</span>
        <span className="ml-auto flex items-center gap-2 font-mono text-xs">
          <span
            className={cx(
              "inline-flex h-2 w-2 rounded-full",
              response.status < 400 ? "bg-success" : "bg-danger",
            )}
          />
          <span className="text-foreground">
            {response.status} {response.statusText}
          </span>
        </span>
      </div>

      {/* side toggle */}
      <div className="flex gap-1 border-b border-border bg-surface/50 p-1.5">
        {(["request", "response"] as Side[]).map((s) => (
          <button
            key={s}
            onClick={() => setCurrentSide(s)}
            className={cx(
              "flex-1 rounded-lg px-3 py-2 font-mono text-xs uppercase tracking-widest transition-colors",
              side === s ? "bg-card text-cyan" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {s}
          </button>
        ))}
      </div>

      {/* tabs */}
      <div className="flex items-center gap-1 border-b border-border px-3 py-2">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cx(
              "rounded-md px-3 py-1.5 text-xs font-medium capitalize transition-colors",
              tab === t ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {/* content */}
      <div className="max-h-[360px] overflow-auto p-4 no-scrollbar">
        {isReq && tab === "overview" && (
          <dl className="space-y-2 font-mono text-xs">
            <Row k="Method" v={request.method} />
            <Row k="Host" v={request.host} />
            <Row k="Path" v={request.path} />
            <Row k="Cookies" v={request.headers.Cookie ?? "—"} />
          </dl>
        )}
        {isReq && tab === "headers" && <HeaderRows headers={request.headers} />}
        {isReq && tab === "query" && (
          <dl className="space-y-2 font-mono text-xs">
            {Object.entries(request.query).map(([k, v]) => (
              <Row key={k} k={k} v={v} />
            ))}
          </dl>
        )}

        {!isReq && tab === "overview" && (
          <div className="space-y-4">
            <dl className="space-y-2 font-mono text-xs">
              <Row k="Status" v={`${response.status} ${response.statusText}`} />
              <Row k="Content-Type" v={response.headers["Content-Type"] ?? "—"} />
            </dl>
            {response.cookieIssues.length > 0 && (
              <div className="rounded-lg border border-warning/30 bg-warning/5 p-3">
                <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-warning">
                  <Icon name="alert" size={12} /> Cookie attribute issues
                </div>
                <ul className="mt-2 space-y-1 font-mono text-xs text-muted-foreground">
                  {response.cookieIssues.map((c) => (
                    <li key={c} className="flex items-center gap-2">
                      <Icon name="x" size={12} className="text-danger" /> {c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {response.missing.length > 0 && (
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <div className="font-mono text-[10px] uppercase tracking-widest text-subtle">
                  Missing security headers
                </div>
                <ul className="mt-2 space-y-1 font-mono text-xs text-muted-foreground">
                  {response.missing.map((m) => (
                    <li key={m} className="flex items-center gap-2">
                      <Icon name="alert" size={12} className="text-warning" /> {m}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {(response.safeSetCookie || response.safeHeaders) && (
              <div className="rounded-lg border border-success/30 bg-success/5 p-3">
                <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-success">
                  <Icon name="shield" size={12} /> Safer response (compare)
                </div>
                <div className="mt-2 space-y-1.5 font-mono text-xs">
                  {response.safeSetCookie && (
                    <div>
                      <span className="text-cyan">Set-Cookie:</span>{" "}
                      <span className="break-all text-success">{response.safeSetCookie}</span>
                    </div>
                  )}
                  {response.safeHeaders &&
                    Object.entries(response.safeHeaders).map(([k, v]) => (
                      <div key={k}>
                        <span className="text-cyan">{k}:</span>{" "}
                        <span className="break-all text-success">{v}</span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}
        {!isReq && tab === "headers" && (
          <HeaderRows
            headers={response.headers}
            flags={{ "Set-Cookie": "warn", Server: "warn" }}
          />
        )}
        {!isReq && tab === "body" && (
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase tracking-widest text-subtle">
                JSON body
              </span>
              <CopyBtn text={JSON.stringify(response.body, null, 2)} onCopied={showToast} />
            </div>
            <pre className="overflow-auto rounded-lg bg-surface p-3 font-mono text-xs leading-relaxed">
              <JsonHighlight value={response.body} />
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex flex-wrap gap-x-2">
      <dt className="text-cyan">{k}:</dt>
      <dd className="break-all text-muted-foreground">{v}</dd>
    </div>
  );
}
