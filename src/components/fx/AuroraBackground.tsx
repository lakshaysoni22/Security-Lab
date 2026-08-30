import type { CSSProperties } from "react";
import { usePrefersReducedMotion } from "../../context/AppContext";

/**
 * Fixed, low-opacity animated ground rendered once behind the whole app.
 * Slow-drifting colour blobs + a faint grid + fine noise. Static under
 * reduced-motion. Purely decorative and non-interactive.
 *
 * Performance: uses contain:strict, GPU-promoted layers, and smaller
 * blobs on mobile to keep frame rates smooth on lower-end devices.
 */
export function AuroraBackground() {
  const reduced = usePrefersReducedMotion();
  const blob = (extra: CSSProperties, dur: number, delay = 0): CSSProperties => ({
    position: "absolute",
    borderRadius: "9999px",
    filter: "blur(90px)",
    transform: "translateZ(0)",
    backfaceVisibility: "hidden",
    willChange: reduced ? undefined : "transform",
    animation: reduced ? undefined : `aurora-drift ${dur}s ease-in-out ${delay}s infinite`,
    ...extra,
  });

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      style={{ background: "var(--color-background)", contain: "strict" }}
    >
      <div
        style={blob(
          {
            top: "-12%",
            left: "-8%",
            width: "min(48vw, 500px)",
            height: "min(48vw, 500px)",
            background: "radial-gradient(closest-side, rgba(47,107,255,0.20), transparent)",
          },
          38,
        )}
      />
      <div
        style={blob(
          {
            top: "20%",
            right: "-12%",
            width: "min(42vw, 440px)",
            height: "min(42vw, 440px)",
            background: "radial-gradient(closest-side, rgba(34,211,238,0.16), transparent)",
          },
          46,
          -6,
        )}
      />
      <div
        style={blob(
          {
            bottom: "-18%",
            left: "25%",
            width: "min(44vw, 460px)",
            height: "min(44vw, 460px)",
            background: "radial-gradient(closest-side, rgba(139,92,246,0.14), transparent)",
          },
          54,
          -12,
        )}
      />
      {/* faint grid */}
      <div className="absolute inset-0 bg-grid opacity-[0.4]" />
      {/* fine noise via SVG data-uri */}
      <div
        className="absolute inset-0 opacity-[0.035] mix-blend-overlay"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
        }}
      />
      {/* top vignette so content stays legible */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 90% 60% at 50% -10%, transparent 40%, var(--color-background) 100%)",
        }}
      />
    </div>
  );
}
