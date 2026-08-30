import { Suspense, lazy } from "react";
import { useApp, usePrefersReducedMotion } from "../../context/AppContext";
import { Icon } from "../ui/Icon";
import { PremiumButton } from "../ui/primitives";

const CyberNetwork = lazy(() =>
  import("./CyberNetwork").then((m) => ({ default: m.CyberNetwork })),
);

function OrbitVisual() {
  const reduced = usePrefersReducedMotion();
  const rings = [
    { size: 340, dur: 46, dir: 1 },
    { size: 250, dur: 34, dir: -1 },
    { size: 170, dur: 24, dir: 1 },
  ];
  return (
    <div className="pointer-events-none absolute inset-0 grid place-items-center">
      {rings.map((r, i) => (
        <div
          key={i}
          className="absolute rounded-full border border-cyan/15"
          style={{
            width: r.size,
            height: r.size,
            animation: reduced
              ? undefined
              : `spin ${r.dur}s linear infinite ${r.dir > 0 ? "normal" : "reverse"}`,
          }}
        >
          <span
            className="absolute h-2 w-2 rounded-full bg-cyan"
            style={{
              top: -4,
              left: "50%",
              boxShadow: "0 0 12px 2px rgba(34,211,238,0.8)",
            }}
          />
        </div>
      ))}
      <div className="relative grid h-28 w-28 place-items-center rounded-3xl bg-primary/10 text-cyan ring-1 ring-cyan/40 backdrop-blur-sm glow-cyan">
        <Icon name="shield" size={52} strokeWidth={1.4} />
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

const canvasSkeleton = (
  <div
    className="absolute inset-0"
    aria-hidden="true"
    style={{
      background:
        "linear-gradient(100deg, transparent 20%, rgba(34,211,238,0.06) 50%, transparent 80%)",
      backgroundSize: "200% 100%",
      animation: "shimmer 1.6s linear infinite",
    }}
  />
);

export function Hero() {
  const { navigate } = useApp();

  return (
    <section className="relative overflow-hidden pt-28 pb-20 sm:pt-36 sm:pb-28">
      {/* ambient background */}
      <div className="absolute inset-0 bg-grid bg-grid-fade" aria-hidden="true" />
      <div
        className="absolute -top-40 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full opacity-60 blur-3xl"
        style={{
          background:
            "radial-gradient(closest-side, rgba(47,107,255,0.28), rgba(34,211,238,0.10), transparent)",
        }}
        aria-hidden="true"
      />

      <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 sm:px-8 lg:grid-cols-[1.05fr_0.95fr]">
        {/* LEFT */}
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan/25 bg-cyan/5 px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.25em] text-cyan">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan" style={{ animation: "pulse-ring 2s infinite" }} />
            TrinetLayer Cyber Labs
          </div>

          <h1 className="mt-6 font-display text-4xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
            <span className="text-foreground">Learn Cybersecurity.</span>
            <br />
            <span className="text-gradient">Think Like a Defender.</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground">
            Investigate real vulnerabilities inside safe, simulated environments. Five hands-on
            labs take you from your first login flaw to reading raw HTTP on the wire — building
            defender instinct, not just theory.
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <PremiumButton size="lg" iconRight="arrow-right" onClick={() => navigate({ name: "lab", labId: "auth" })}>
              Start Your First Lab
            </PremiumButton>
            <PremiumButton size="lg" variant="outline" icon="route" onClick={() => navigate({ name: "learning" })}>
              Explore Learning Path
            </PremiumButton>
          </div>

          <div className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-4 font-mono text-xs text-muted-foreground">
            <span className="flex items-center gap-2">
              <Icon name="layers" size={15} className="text-cyan" /> 5 Investigations
            </span>
            <span className="flex items-center gap-2">
              <Icon name="shield" size={15} className="text-cyan" /> Safe Simulation
            </span>
            <span className="flex items-center gap-2">
              <Icon name="gauge" size={15} className="text-cyan" /> Progressive Difficulty
            </span>
          </div>
        </div>

        {/* RIGHT: interactive visual */}
        <div className="relative">
          <div className="hud-corner relative mx-auto aspect-square w-full max-w-[460px] overflow-hidden rounded-3xl bg-surface/60 hairline">
            <Suspense fallback={canvasSkeleton}>
              <CyberNetwork />
            </Suspense>
            <OrbitVisual />
            {/* corner telemetry */}
            <div className="absolute left-4 top-4 flex items-center gap-1.5 rounded-lg glass px-2.5 py-1.5 font-mono text-[10px] text-cyan">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan" style={{ animation: "pulse-ring 2s infinite" }} />
              MESH · ONLINE
            </div>
            <div className="absolute bottom-4 right-4 rounded-lg glass px-2.5 py-1.5 font-mono text-[10px] text-muted-foreground">
              nodes: live
            </div>
            {/* floating telemetry chips */}
            {[
              { txt: "TLS 1.3", top: "22%", right: "8%", d: 0.2 },
              { txt: "AES-256", bottom: "26%", left: "6%", d: 0.5 },
              { txt: "SHA-256", top: "58%", right: "10%", d: 0.8 },
            ].map((c) => (
              <div
                key={c.txt}
                className="animate-fade-slide absolute rounded-md border border-cyan/20 bg-card/70 px-2 py-1 font-mono text-[9px] uppercase tracking-wider text-cyan/90 backdrop-blur-sm"
                style={{ top: c.top, bottom: c.bottom, left: c.left, right: c.right, animationDelay: `${c.d}s` }}
              >
                {c.txt}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
