import { useApp } from "../context/AppContext";
import { Icon } from "../components/ui/Icon";
import type { IconName } from "../components/ui/Icon";
import {
  GlowCard,
  PremiumButton,
  Reveal,
  SectionHeader,
  accentHex,
  accentText,
  cx,
} from "../components/ui/primitives";

const LOOP: Array<{ icon: IconName; title: string; body: string; accent: string }> = [
  { icon: "book", title: "Learn", body: "Each lab briefs the concept in plain language before you touch anything.", accent: "cyan" },
  { icon: "cpu", title: "Practice", body: "Interact with a faithful, in-browser simulation of a vulnerable app.", accent: "primary" },
  { icon: "search", title: "Investigate", body: "Gather evidence, form a hypothesis, and prove the flaw yourself.", accent: "violet" },
  { icon: "lightbulb", title: "Understand", body: "Every completion explains why it matters and the defender's fix.", accent: "warning" },
  { icon: "gauge", title: "Improve", body: "Scores, a skill matrix and achievements track your growth over time.", accent: "success" },
];

const CAPABILITIES: Array<{ icon: IconName; title: string; body: string }> = [
  { icon: "layers", title: "A reusable lab engine", body: "One consistent investigation loop powers every lab, so new cases stay easy to add and easy to learn." },
  { icon: "shield", title: "Safe-by-design simulation", body: "All targets are fictional and run locally. The platform never touches real websites, servers, or accounts." },
  { icon: "route", title: "Guided progression", body: "Difficulty ramps from a weak login to raw HTTP analysis, each skill building on the last." },
  { icon: "sparkles", title: "100% private and offline", body: "Deterministic scoring and skill evaluation with zero external API dependencies — fully client-side." },
  { icon: "bar-chart", title: "Progress you can see", body: "A command-center dashboard, skill radar, and achievements make mastery visible." },
  { icon: "eye", title: "Defender mindset", body: "You learn attacks well enough to stop them — the goal is always the fix." },
];

export function About() {
  const { navigate } = useApp();
  return (
    <div className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <SectionHeader
        eyebrow="About"
        title="A cyber range built for learning, not liability"
        description="Cyber Labs is a hands-on cybersecurity training platform designed for security enthusiasts and learners. We turn application-security knowledge into guided investigations so you can learn to think like a defender."
      />

      <Reveal className="mt-10">
        <div className="rounded-2xl border border-cyan/20 bg-cyan/5 p-6">
          <div className="flex items-start gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-cyan/15 text-cyan">
              <Icon name="shield" size={20} />
            </span>
            <p className="text-sm leading-relaxed text-muted-foreground">
              <span className="font-semibold text-foreground">An honest note:</span> this is an
              educational platform built for security researchers, bug hunters,
              and application-security engineers in training. The organisations, portals, and records
              in every lab are fictional and exist only to teach. Nothing here interacts with real
              infrastructure, and no real scanning or attacks are performed.
            </p>
          </div>
        </div>
      </Reveal>

      <div className="mt-16">
        <h3 className="font-display text-2xl font-semibold">The learning loop</h3>
        <div className="mt-8 grid gap-4 md:grid-cols-3 lg:grid-cols-5">
          {LOOP.map((s, i) => (
            <Reveal key={s.title} delay={i * 70}>
              <div className="h-full rounded-2xl bg-card hairline p-6">
                <span
                  className={cx("grid h-11 w-11 place-items-center rounded-xl", accentText(s.accent))}
                  style={{ background: `color-mix(in srgb, ${accentHex(s.accent)} 12%, transparent)` }}
                >
                  <Icon name={s.icon} size={22} />
                </span>
                <h4 className="mt-4 font-semibold text-foreground">{s.title}</h4>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>

      <div className="mt-16">
        <h3 className="font-display text-2xl font-semibold">What powers the platform</h3>
        <div className="mt-8 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map((c, i) => (
            <Reveal key={c.title} delay={i * 60}>
              <GlowCard className="h-full p-6">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-cyan/10 text-cyan">
                  <Icon name={c.icon} size={22} />
                </span>
                <h4 className="mt-4 font-semibold text-foreground">{c.title}</h4>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{c.body}</p>
              </GlowCard>
            </Reveal>
          ))}
        </div>
      </div>

      <Reveal className="mt-16">
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-gradient-to-br from-card to-surface hairline p-8">
          <div>
            <h3 className="font-display text-xl font-semibold">Ready to open your first case?</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Start with the weak front door — no setup, no risk.
            </p>
          </div>
          <div className="flex gap-3">
            <PremiumButton iconRight="arrow-right" onClick={() => navigate({ name: "lab", labId: "auth" })}>
              Start lab 01
            </PremiumButton>
            <PremiumButton variant="outline" icon="shield" onClick={() => navigate({ name: "safety" })}>
              Safety model
            </PremiumButton>
          </div>
        </div>
      </Reveal>
    </div>
  );
}
