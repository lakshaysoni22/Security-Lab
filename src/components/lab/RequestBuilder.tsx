import { useState } from "react";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

export interface MockEndpoint {
  method: string;
  path: string;
  /** Headers that affect the response (checked on match). */
  matchHeaders?: Record<string, string>;
  response: {
    status: number;
    statusText: string;
    headers: Record<string, string>;
    body: string;
  };
  /** Tag fired on interaction. */
  tag?: string;
  /** Reveals CTF flag. */
  revealsFlag?: boolean;
}

interface RequestBuilderProps {
  /** Base URL shown in the builder. */
  baseUrl: string;
  /** Available mock endpoints. */
  endpoints: MockEndpoint[];
  /** Callback when a request is sent. */
  onRequest?: (method: string, path: string, tag?: string) => void;
  /** Callback when flag is revealed. */
  onFlagReveal?: () => void;
  className?: string;
}

const METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"];
const METHOD_COLOR: Record<string, string> = {
  GET: "text-success",
  POST: "text-primary",
  PUT: "text-warning",
  DELETE: "text-danger",
  PATCH: "text-violet",
};

/** Mini Postman — build and send HTTP requests to simulated endpoints. */
export function RequestBuilder({
  baseUrl,
  endpoints,
  onRequest,
  onFlagReveal,
  className,
}: RequestBuilderProps) {
  const [method, setMethod] = useState("GET");
  const [path, setPath] = useState(endpoints[0]?.path ?? "/");
  const [headers, setHeaders] = useState<Array<{ key: string; value: string }>>([
    { key: "Content-Type", value: "application/json" },
  ]);
  const [body, setBody] = useState("");
  const [response, setResponse] = useState<MockEndpoint["response"] | null>(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<"headers" | "body" | "response">("headers");

  const addHeader = () => setHeaders((h) => [...h, { key: "", value: "" }]);
  const removeHeader = (i: number) => setHeaders((h) => h.filter((_, j) => j !== i));
  const updateHeader = (i: number, field: "key" | "value", val: string) => {
    setHeaders((h) => h.map((row, j) => (j === i ? { ...row, [field]: val } : row)));
  };

  const send = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 300 + Math.random() * 500));

    // Match endpoint
    const match = endpoints.find((ep) => {
      if (ep.method !== method) return false;
      // Simple path matching — supports /records/:id style
      const epParts = ep.path.split("/");
      const reqParts = path.split("/");
      if (epParts.length !== reqParts.length) return false;
      return epParts.every((p, i) => p.startsWith(":") || p === reqParts[i]);
    });

    if (match) {
      setResponse(match.response);
      onRequest?.(method, path, match.tag);
      if (match.revealsFlag) onFlagReveal?.();
    } else {
      setResponse({
        status: 404,
        statusText: "Not Found",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ error: "Endpoint not found", path }, null, 2),
      });
    }

    setLoading(false);
    setTab("response");
  };

  const statusColor = (code: number) => {
    if (code < 300) return "text-success";
    if (code < 400) return "text-cyan";
    if (code < 500) return "text-warning";
    return "text-danger";
  };

  return (
    <div
      className={cx(
        "overflow-hidden rounded-2xl border border-border bg-[#0a0c14] shadow-xl",
        className,
      )}
    >
      {/* URL bar */}
      <div className="flex items-center gap-2 border-b border-border/60 bg-surface/80 px-3 py-2.5 sm:px-4">
        <select
          value={method}
          onChange={(e) => setMethod(e.target.value)}
          className={cx(
            "rounded-md border border-border bg-background px-2 py-1.5 font-mono text-xs font-bold outline-none",
            METHOD_COLOR[method],
          )}
        >
          {METHODS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        <div className="flex flex-1 items-center rounded-lg border border-border bg-background px-3 py-1.5">
          <span className="shrink-0 font-mono text-[10px] text-subtle">{baseUrl}</span>
          <input
            value={path}
            onChange={(e) => setPath(e.target.value)}
            className="flex-1 bg-transparent font-mono text-xs text-foreground outline-none caret-cyan"
            spellCheck={false}
            aria-label="Request path"
          />
        </div>
        <button
          onClick={send}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 font-mono text-[11px] font-bold uppercase tracking-wider text-white hover:bg-primary/80 active:scale-95 transition-all disabled:opacity-50"
        >
          {loading ? (
            <>
              <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />{" "}
              Sending
            </>
          ) : (
            <>
              <Icon name="zap" size={12} /> Send
            </>
          )}
        </button>
      </div>

      {/* tabs */}
      <div className="flex border-b border-border/40">
        {(["headers", "body", "response"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cx(
              "flex-1 px-4 py-2 font-mono text-[11px] uppercase tracking-widest transition-colors",
              tab === t
                ? "border-b-2 border-cyan text-cyan"
                : "text-subtle hover:text-muted-foreground",
            )}
          >
            {t}
            {t === "response" && response && (
              <span
                className={cx(
                  "ml-2 rounded-full px-1.5 py-0.5 text-[9px]",
                  statusColor(response.status),
                )}
              >
                {response.status}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* tab content */}
      <div className="max-h-[350px] overflow-auto p-4 no-scrollbar sm:max-h-[400px]">
        {tab === "headers" && (
          <div className="space-y-2">
            {headers.map((h, i) => (
              <div key={i} className="flex items-center gap-2">
                <input
                  value={h.key}
                  onChange={(e) => updateHeader(i, "key", e.target.value)}
                  placeholder="Header name"
                  className="w-1/3 rounded-md border border-border bg-background/60 px-2 py-1.5 font-mono text-xs text-foreground outline-none focus:border-cyan/50"
                  spellCheck={false}
                />
                <input
                  value={h.value}
                  onChange={(e) => updateHeader(i, "value", e.target.value)}
                  placeholder="Value"
                  className="flex-1 rounded-md border border-border bg-background/60 px-2 py-1.5 font-mono text-xs text-foreground outline-none focus:border-cyan/50"
                  spellCheck={false}
                />
                <button
                  onClick={() => removeHeader(i)}
                  className="rounded-md p-1 text-subtle hover:text-danger"
                >
                  <Icon name="x" size={14} />
                </button>
              </div>
            ))}
            <button
              onClick={addHeader}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 font-mono text-[10px] text-cyan hover:bg-cyan/10"
            >
              <Icon name="plus" size={12} /> Add Header
            </button>
          </div>
        )}

        {tab === "body" && (
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder='{"username": "admin", "password": "test123"}'
            className="min-h-[150px] w-full resize-none rounded-lg border border-border bg-background/60 p-3 font-mono text-xs text-foreground outline-none caret-cyan placeholder:text-subtle focus:border-cyan/50"
            spellCheck={false}
          />
        )}

        {tab === "response" && (
          <div>
            {response ? (
              <>
                <div className="mb-3 flex items-center gap-3">
                  <span
                    className={cx(
                      "rounded-md px-2 py-1 font-mono text-sm font-bold",
                      statusColor(response.status),
                    )}
                  >
                    {response.status}
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">
                    {response.statusText}
                  </span>
                </div>
                {/* response headers */}
                <div className="mb-3 rounded-lg border border-border/40 bg-surface/30 p-3">
                  <div className="mb-1 font-mono text-[9px] uppercase tracking-widest text-subtle">
                    Response Headers
                  </div>
                  {Object.entries(response.headers).map(([k, v]) => (
                    <div key={k} className="font-mono text-[11px]">
                      <span className="text-cyan">{k}:</span>{" "}
                      <span className="text-foreground/80">{v}</span>
                    </div>
                  ))}
                </div>
                {/* response body */}
                <div className="rounded-lg border border-border/40 bg-surface/30 p-3">
                  <div className="mb-1 font-mono text-[9px] uppercase tracking-widest text-subtle">
                    Response Body
                  </div>
                  <pre className="whitespace-pre-wrap break-all font-mono text-xs leading-relaxed text-foreground/90">
                    {response.body}
                  </pre>
                </div>
              </>
            ) : (
              <div className="py-8 text-center text-sm text-subtle">
                Send a request to see the response
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
