import { useEffect, useRef, useState } from "react";
import { Icon } from "../ui/Icon";
import { cx } from "../ui/primitives";

/** Thin top progress bar + a scroll-to-top affordance. Throttled for perf. */
export function ScrollProgress() {
  const [pct, setPct] = useState(0);
  const [show, setShow] = useState(false);
  const raf = useRef(0);

  useEffect(() => {
    const onScroll = () => {
      if (raf.current) return;
      raf.current = requestAnimationFrame(() => {
        const el = document.documentElement;
        const max = el.scrollHeight - el.clientHeight;
        const y = el.scrollTop;
        setPct(max > 0 ? (y / max) * 100 : 0);
        setShow(y > 600);
        raf.current = 0;
      });
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, []);

  return (
    <>
      <div className="pointer-events-none fixed inset-x-0 top-0 z-[70] h-0.5">
        <div
          className="h-full origin-left transition-transform duration-150"
          style={{
            transform: `scaleX(${pct / 100})`,
            background: "linear-gradient(90deg, #2f6bff, #22d3ee, #8b5cf6)",
          }}
        />
      </div>
      <button
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        aria-label="Scroll to top"
        className={cx(
          "fixed bottom-6 right-6 z-[60] grid h-11 w-11 place-items-center rounded-xl glass text-cyan transition-all duration-300 hover:border-cyan/50 hover:-translate-y-0.5 active:scale-95",
          show ? "opacity-100" : "pointer-events-none translate-y-2 opacity-0",
        )}
      >
        <Icon name="chevron-down" size={18} className="rotate-180" />
      </button>
    </>
  );
}
