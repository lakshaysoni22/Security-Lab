import { useApp } from "../context/AppContext";
import { LABS } from "../lib/labs";
import { Icon } from "../components/ui/Icon";
import type { IconName } from "../components/ui/Icon";
import {
  PremiumButton,
  Reveal,
  SectionHeader,
  accentText,
  cx,
} from "../components/ui/primitives";

const PRINCIPLES: Array<{ icon: IconName; title: string; body: string }> = [
  { icon: "cpu", title: "Everything is simulated", body: "Each target is an in-memory, in-browser recreation of a vulnerable app. There is no backend to attack." },
  { icon: "globe", title: "No external targets", body: "The platform never contacts real websites, servers, accounts, IPs, or third-party systems." },
  { icon: "lock", title: "No unrestricted networking", body: "Labs don't issue arbitrary network requests. All responses are scripted and deterministic." },
  { icon: "key", title: "No secrets in scope", body: "Any credentials or tokens shown are fictional examples. Nothing real is ever stored or transmitted." },
];

const ROWS: Array<{ key: keyof NonNullable<(typeof LABS)[number]["security"]>; label: string }> = [
  { key: "asset", label: "Asset" },
  { key: "threat", label: "Threat" },
  { key: "weakness", label: "Weakness" },
  { key: "safeBoundary", label: "Safe boundary" },
  { key: "successCondition", label: "Success condition" },
  { key: "remediation", label: "Remediation" },
];

export function Safety() {
  const { navigate } = useApp();
  return (
    <div className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <SectionHeader
        eyebrow="Safety Model"
        title="Real vulnerabilities. Zero real risk."
        description="Cyber Labs is an educational simulation. Every technique you practise is genuine — but it only ever runs against fictional, local targets designed to be broken."
      />

      <Reveal className="mt-10">
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-success/25 bg-success/5 p-5">
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-success/15 text-success">
            <Icon name="shield" size={22} />
          </span>
          <div>
            <div className="font-display text-lg font-semibold text-foreground">
              Educational Simulation — No External Targets
            </div>
            <p className="mt-0.5 text-sm text-muted-foreground">
              This platform is for learning to defend systems. Applying these techniques to
              systems you do not own or have explicit permission to test is illegal.
            </p>
          </div>
        </div>
      </Reveal>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {PRINCIPLES.map((p, i) => (
          <Reveal key={p.title} delay={i * 70}>
            <div className="h-full rounded-2xl bg-card hairline p-5">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-cyan/10 text-cyan">
                <Icon name={p.icon} size={20} />
              </span>
              <h3 className="mt-3 text-sm font-semibold text-foreground">{p.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{p.body}</p>
            </div>
          </Reveal>
        ))}
      </div>

      <div className="mt-16">
        <h3 className="font-display text-2xl font-semibold">Per-lab threat models</h3>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Each lab documents exactly what it teaches and the boundary that keeps it safe.
        </p>

        <div className="mt-8 space-y-5">
          {LABS.map((lab, i) => {
            const s = lab.security;
            if (!s) return null;
            return (
              <Reveal key={lab.id} delay={i * 50}>
                <div className="overflow-hidden rounded-2xl bg-card hairline">
                  <div className="flex flex-wrap items-center gap-3 border-b border-border/70 p-5">
                    <span className={cx("font-display text-lg font-bold", accentText(lab.accent))}>
                      {String(lab.number).padStart(2, "0")}
                    </span>
                    <div>
                      <div className="font-semibold text-foreground">
                        {lab.codename} — {lab.title}
                      </div>
                      <div className="font-mono text-[11px] uppercase tracking-widest text-subtle">
                        {lab.category} · learning goal: {s.learningGoal}
                      </div>
                    </div>
                    <PremiumButton
                      size="sm"
                      variant="outline"
                      className="ml-auto"
                      iconRight="arrow-right"
                      onClick={() => navigate({ name: "lab", labId: lab.id })}
                    >
                      Open lab
                    </PremiumButton>
                  </div>
                  <dl className="grid gap-px bg-border/60 sm:grid-cols-2 lg:grid-cols-3">
                    {ROWS.map((row) => (
                      <div key={row.key} className="bg-card p-4">
                        <dt className="font-mono text-[10px] uppercase tracking-widest text-cyan">
                          {row.label}
                        </dt>
                        <dd className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                          {s[row.key]}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </div>
  );
}
