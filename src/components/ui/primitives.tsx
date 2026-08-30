import {
  useEffect,
  useRef,
  useState,
} from "react";
import type { ButtonHTMLAttributes, CSSProperties, PointerEvent as ReactPointerEvent, ReactNode } from "react";
import { Icon } from "./Icon";
import type { IconName } from "./Icon";
import type { Difficulty, LabStatus } from "../../lib/types";

/* ------------------------------------------------------------------ utils */

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

const ACCENT_TEXT: Record<string, string> = {
  cyan: "text-cyan",
  primary: "text-primary",
  violet: "text-violet",
  warning: "text-warning",
  success: "text-success",
};
const ACCENT_HEX: Record<string, string> = {
  cyan: "#22d3ee",
  primary: "#2f6bff",
  violet: "#8b5cf6",
  warning: "#fbbf24",
  success: "#34d399",
};
export function accentText(a: string) {
  return ACCENT_TEXT[a] ?? "text-cyan";
}
export function accentHex(a: string) {
  return ACCENT_HEX[a] ?? "#22d3ee";
}

/* ------------------------------------------------------------- useInView */

/** Shared IntersectionObserver hook — fires once when the element scrolls in. */
export function useInView<T extends Element = HTMLDivElement>(
  opts: IntersectionObserverInit = { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
) {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          setInView(true);
          io.disconnect();
        }
      });
    }, opts);
    io.observe(el);
    return () => io.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return { ref, inView };
}

/* --------------------------------------------------------------- Reveal */

export function Reveal({
  children,
  delay = 0,
  className,
  as: Tag = "div",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: "div" | "section" | "li" | "article";
}) {
  const { ref, inView } = useInView<HTMLElement>();
  const Comp = Tag as "div";
  return (
    <Comp
      ref={ref as never}
      className={cx("reveal", inView && "is-visible", className)}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </Comp>
  );
}

/* --------------------------------------------------------------- CountUp */

function usePrefersReduced() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}

/** Counts a number up from 0 → value once scrolled into view. */
export function CountUp({
  value,
  duration = 1100,
  prefix = "",
  suffix = "",
  className,
}: {
  value: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}) {
  const { ref, inView } = useInView<HTMLSpanElement>();
  const reduced = usePrefersReduced();
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!inView) return;
    if (reduced || value === 0) {
      setN(value);
      return;
    }
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setN(Math.round(value * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration, reduced]);
  return (
    <span ref={ref} className={className}>
      {prefix}
      {n}
      {suffix}
    </span>
  );
}

/* ------------------------------------------------------------------ Tilt */

/** Subtle pointer-driven 3D tilt + glare. Disabled on touch / reduced-motion. */
export function Tilt({
  children,
  className,
  max = 6,
}: {
  children: ReactNode;
  className?: string;
  max?: number;
}) {
  const reduced = usePrefersReduced();
  const ref = useRef<HTMLDivElement | null>(null);
  const [style, setStyle] = useState<CSSProperties>({});
  const [glare, setGlare] = useState<CSSProperties>({ opacity: 0 });

  if (reduced) return <div className={className}>{children}</div>;

  const onMove = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (e.pointerType === "touch") return;
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    const rx = (0.5 - py) * max * 2;
    const ry = (px - 0.5) * max * 2;
    setStyle({
      transform: `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg)`,
      transition: "transform 0.08s ease-out",
    });
    setGlare({
      opacity: 1,
      background: `radial-gradient(circle at ${px * 100}% ${py * 100}%, rgba(255,255,255,0.12), transparent 45%)`,
    });
  };
  const reset = () => {
    setStyle({ transform: "perspective(900px) rotateX(0) rotateY(0)", transition: "transform 0.4s ease" });
    setGlare({ opacity: 0 });
  };

  return (
    <div
      ref={ref}
      onPointerMove={onMove}
      onPointerLeave={reset}
      className={cx("relative", className)}
      style={{ ...style, transformStyle: "preserve-3d" }}
    >
      {children}
      <div
        className="pointer-events-none absolute inset-0 z-10 rounded-2xl transition-opacity duration-200"
        style={glare}
        aria-hidden="true"
      />
    </div>
  );
}

/* -------------------------------------------------------- PremiumButton */

type BtnVariant = "primary" | "ghost" | "outline" | "subtle";

interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: BtnVariant;
  icon?: IconName;
  iconRight?: IconName;
  size?: "sm" | "md" | "lg";
}

export function PremiumButton({
  variant = "primary",
  icon,
  iconRight,
  size = "md",
  className,
  children,
  ...rest
}: BtnProps) {
  const sizes = {
    sm: "h-9 px-3.5 text-sm gap-1.5",
    md: "h-11 px-5 text-sm gap-2",
    lg: "h-13 px-7 text-base gap-2.5 py-3.5",
  }[size];

  const variants: Record<BtnVariant, string> = {
    primary:
      "bg-primary text-primary-foreground glow-primary hover:brightness-110 hover:-translate-y-0.5 active:translate-y-0",
    ghost: "text-foreground/80 hover:text-foreground hover:bg-muted/60",
    outline:
      "hairline text-foreground hover:border-cyan/60 hover:text-cyan hover:bg-cyan/5 hover:-translate-y-0.5",
    subtle: "bg-muted text-foreground hover:bg-elevated",
  };

  return (
    <button
      className={cx(
        "inline-flex items-center justify-center rounded-xl font-medium tracking-tight",
        "transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:translate-y-0",
        sizes,
        variants[variant],
        className,
      )}
      {...rest}
    >
      {icon && <Icon name={icon} size={size === "lg" ? 20 : 18} />}
      {children}
      {iconRight && <Icon name={iconRight} size={size === "lg" ? 20 : 18} />}
    </button>
  );
}

/* ----------------------------------------------------------- GlassPanel */

export function GlassPanel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cx("glass rounded-2xl", className)}>{children}</div>;
}

/* ------------------------------------------------------------- GlowCard */

export function GlowCard({
  children,
  className,
  accent = "cyan",
  interactive = true,
}: {
  children: ReactNode;
  className?: string;
  accent?: string;
  interactive?: boolean;
}) {
  return (
    <div
      className={cx(
        "group relative rounded-2xl bg-card hairline overflow-hidden",
        interactive && "transition-all duration-300 hover:-translate-y-1 hover:border-transparent",
        className,
      )}
      style={{ ["--acc" as string]: accentHex(accent) }}
    >
      {interactive && (
        <div
          className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
          style={{
            boxShadow: `0 0 0 1px color-mix(in srgb, ${accentHex(accent)} 45%, transparent), 0 24px 60px -24px color-mix(in srgb, ${accentHex(accent)} 55%, transparent)`,
          }}
        />
      )}
      <div className="relative">{children}</div>
    </div>
  );
}

/* --------------------------------------------------------- SectionHeader */

export function SectionHeader({
  eyebrow,
  index,
  title,
  description,
  align = "left",
  className,
}: {
  eyebrow?: string;
  index?: string;
  title: ReactNode;
  description?: ReactNode;
  align?: "left" | "center";
  className?: string;
}) {
  return (
    <div
      className={cx(
        "max-w-2xl",
        align === "center" && "mx-auto text-center",
        className,
      )}
    >
      {(eyebrow || index) && (
        <div
          className={cx(
            "mb-4 flex items-center gap-3 font-mono text-xs uppercase tracking-[0.25em] text-cyan",
            align === "center" && "justify-center",
          )}
        >
          {index && <span className="text-subtle">{index}</span>}
          {eyebrow && <span>{eyebrow}</span>}
          <span className="h-px w-8 bg-cyan/50" />
        </div>
      )}
      <h2 className="text-3xl font-semibold leading-tight text-foreground sm:text-4xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-base leading-relaxed text-muted-foreground">{description}</p>
      )}
    </div>
  );
}

/* --------------------------------------------------------- Status badges */

const STATUS_META: Record<
  LabStatus,
  { label: string; cls: string; icon: IconName }
> = {
  locked: { label: "Locked", cls: "text-subtle bg-muted/50", icon: "lock" },
  available: { label: "Available", cls: "text-cyan bg-cyan/10", icon: "play" },
  "in-progress": { label: "In Progress", cls: "text-warning bg-warning/10", icon: "activity" },
  completed: { label: "Completed", cls: "text-success bg-success/10", icon: "check-circle" },
};

export function StatusBadge({ status }: { status: LabStatus }) {
  const m = STATUS_META[status];
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-mono text-[11px] font-medium uppercase tracking-wider",
        m.cls,
      )}
    >
      <Icon name={m.icon} size={12} strokeWidth={2} />
      {m.label}
    </span>
  );
}

const DIFF_META: Record<Difficulty, string> = {
  Beginner: "text-success border-success/30",
  Intermediate: "text-warning border-warning/30",
  Advanced: "text-danger border-danger/30",
};

export function DifficultyBadge({ level }: { level: Difficulty }) {
  const dots = level === "Beginner" ? 1 : level === "Intermediate" ? 2 : 3;
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[11px] uppercase tracking-wider",
        DIFF_META[level],
      )}
    >
      <span className="flex gap-0.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className={cx("h-1 w-1 rounded-full", i < dots ? "bg-current" : "bg-current/25")}
          />
        ))}
      </span>
      {level}
    </span>
  );
}

export function Chip({
  children,
  icon,
  className,
}: {
  children: ReactNode;
  icon?: IconName;
  className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-md bg-muted/60 px-2 py-1 font-mono text-[11px] text-muted-foreground",
        className,
      )}
    >
      {icon && <Icon name={icon} size={12} />}
      {children}
    </span>
  );
}

/* -------------------------------------------------------- ProgressRing */

export function ProgressRing({
  value,
  size = 160,
  stroke = 12,
  accent = "cyan",
  label,
  sublabel,
  animate = true,
}: {
  value: number; // 0..100
  size?: number;
  stroke?: number;
  accent?: string;
  label?: ReactNode;
  sublabel?: ReactNode;
  animate?: boolean;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const [shown, setShown] = useState(animate ? 0 : value);
  useEffect(() => {
    if (!animate) {
      setShown(value);
      return;
    }
    const t = setTimeout(() => setShown(value), 120);
    return () => clearTimeout(t);
  }, [value, animate]);
  const off = c - (Math.min(100, Math.max(0, shown)) / 100) * c;
  const hex = accentHex(accent);
  return (
    <div className="relative inline-grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="var(--color-muted)" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={hex}
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={off}
          style={{
            transition: "stroke-dashoffset 1.1s cubic-bezier(0.22,1,0.36,1)",
            filter: `drop-shadow(0 0 6px color-mix(in srgb, ${hex} 60%, transparent))`,
          }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          {label && <div className="text-3xl font-semibold leading-none text-foreground">{label}</div>}
          {sublabel && (
            <div className="mt-1 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              {sublabel}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------- MetricCard */

export function MetricCard({
  icon,
  value,
  label,
  accent = "cyan",
}: {
  icon: IconName;
  value: ReactNode;
  label: string;
  accent?: string;
}) {
  return (
    <div className="rounded-xl bg-card hairline p-4">
      <div className="flex items-center gap-2 text-muted-foreground">
        <span className={accentText(accent)}>
          <Icon name={icon} size={16} />
        </span>
        <span className="font-mono text-[11px] uppercase tracking-widest">{label}</span>
      </div>
      <div className="mt-2 text-2xl font-semibold text-foreground">{value}</div>
    </div>
  );
}

/* --------------------------------------------------------- ProgressBar */

export function ProgressBar({
  value,
  accent = "cyan",
  className,
}: {
  value: number;
  accent?: string;
  className?: string;
}) {
  return (
    <div className={cx("h-1.5 w-full overflow-hidden rounded-full bg-muted", className)}>
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{
          width: `${Math.min(100, Math.max(0, value))}%`,
          background: `linear-gradient(90deg, ${accentHex(accent)}, color-mix(in srgb, ${accentHex(accent)} 40%, #fff))`,
        }}
      />
    </div>
  );
}
