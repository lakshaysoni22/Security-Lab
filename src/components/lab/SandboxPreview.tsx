import { useRef, useState, useCallback, useEffect } from "react";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

interface SandboxPreviewProps {
  /** HTML input to render in the sandbox. */
  html: string;
  /** Title shown in the frame header. */
  title?: string;
  /** Called when XSS is detected (alert/prompt/confirm). */
  onXSSDetected?: () => void;
  className?: string;
}

/**
 * Isolated sandbox preview — renders user-supplied HTML inside a sandboxed
 * iframe. Intercepts alert/prompt/confirm to detect XSS payloads.
 * Uses srcdoc with sandbox="allow-scripts" for isolation.
 */
export function SandboxPreview({
  html,
  title = "Target Application",
  onXSSDetected,
  className,
}: SandboxPreviewProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [xssDetected, setXssDetected] = useState(false);
  const [alertMessages, setAlertMessages] = useState<string[]>([]);

  const buildSrcdoc = useCallback(
    (inputHtml: string) => {
      // Wrap the HTML in a document that intercepts alert/confirm/prompt
      return `<!DOCTYPE html>
<html>
<head>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f8fafc;
    color: #1e293b;
    padding: 16px;
    font-size: 14px;
    line-height: 1.6;
  }
  .search-box {
    padding: 10px 14px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    width: 100%;
    font-size: 14px;
    margin-bottom: 12px;
  }
  .results {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
  }
  .results h3 { font-size: 13px; color: #64748b; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
  .xss-banner {
    position: fixed; top: 0; left: 0; right: 0;
    background: #dc2626; color: white;
    padding: 8px 16px; font-weight: 600; font-size: 13px;
    text-align: center; z-index: 9999;
    animation: slideDown 0.3s ease;
  }
  @keyframes slideDown { from { transform: translateY(-100%); } to { transform: translateY(0); } }
</style>
<script>
  // Intercept XSS triggers
  const _alert = window.alert;
  const _confirm = window.confirm;
  const _prompt = window.prompt;
  window.alert = function(msg) {
    window.parent.postMessage({ type: 'xss-detected', message: String(msg) }, '*');
    const banner = document.createElement('div');
    banner.className = 'xss-banner';
    banner.textContent = '⚠ XSS Executed: alert("' + msg + '")';
    document.body.prepend(banner);
  };
  window.confirm = function(msg) {
    window.parent.postMessage({ type: 'xss-detected', message: 'confirm: ' + String(msg) }, '*');
    return false;
  };
  window.prompt = function(msg) {
    window.parent.postMessage({ type: 'xss-detected', message: 'prompt: ' + String(msg) }, '*');
    return null;
  };
  window.onerror = function(msg) {
    window.parent.postMessage({ type: 'xss-error', message: String(msg) }, '*');
  };
</script>
</head>
<body>
  <div class="results">
    <h3>Search Results for:</h3>
    <div id="output">${inputHtml}</div>
  </div>
</body>
</html>`;
    },
    [],
  );

  // Listen for messages from the iframe
  const handleMessage = useCallback(
    (e: MessageEvent) => {
      if (e.data?.type === "xss-detected") {
        setXssDetected(true);
        setAlertMessages((prev) => [...prev, e.data.message]);
        onXSSDetected?.();
      }
    },
    [onXSSDetected],
  );

  // Attach message listener
  useEffect(() => {
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [handleMessage]);

  return (
    <div
      className={cx(
        "overflow-hidden rounded-2xl border border-border bg-background shadow-xl",
        className,
      )}
    >
      {/* chrome bar */}
      <div className="flex items-center gap-2 border-b border-border bg-surface px-3 py-2">
        <Icon name="globe" size={13} className="text-cyan" />
        <span className="font-mono text-[11px] text-muted-foreground">{title}</span>
        <div className="ml-auto flex items-center gap-2">
          {xssDetected && (
            <span className="inline-flex items-center gap-1 rounded-full bg-danger/15 px-2 py-0.5 font-mono text-[9px] uppercase text-danger">
              <Icon name="alert" size={10} /> XSS Detected
            </span>
          )}
          <span className="rounded-full bg-warning/10 px-2 py-0.5 font-mono text-[9px] uppercase text-warning">
            Sandboxed
          </span>
        </div>
      </div>

      {/* iframe */}
      <div className="relative min-h-[180px] bg-white">
        <iframe
          ref={iframeRef}
          srcDoc={buildSrcdoc(html)}
          sandbox="allow-scripts"
          title="Sandbox preview"
          className="h-[200px] w-full border-0 sm:h-[250px]"
        />
      </div>

      {/* XSS log */}
      {alertMessages.length > 0 && (
        <div className="border-t border-danger/30 bg-danger/5 px-4 py-3">
          <div className="mb-1 font-mono text-[9px] uppercase tracking-widest text-danger">
            XSS Execution Log
          </div>
          {alertMessages.map((msg, i) => (
            <div key={i} className="font-mono text-[11px] text-danger/80">
              ⚡ alert(&quot;{msg}&quot;) executed
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
