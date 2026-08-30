import { useState } from "react";
import { useApp } from "../context/AppContext";
import { LABS } from "../lib/labs";
import { Hero } from "../components/hero/Hero";
import { LabCard } from "../components/LabCard";
import { SkillRadar } from "../components/SkillRadar";
import { Icon } from "../components/ui/Icon";
import type { IconName } from "../components/ui/Icon";
import {
  CountUp,
  GlowCard,
  PremiumButton,
  ProgressRing,
  Reveal,
  SectionHeader,
  Tilt,
  useInView,
  accentHex,
  accentText,
  cx,
} from "../components/ui/primitives";

function Section({
  id,
  children,
  className,
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={cx("mx-auto max-w-7xl px-5 py-20 sm:px-8 sm:py-28", className)}>
      {children}
    </section>
  );
}

/* 02 — Platform intro / trust band */
function PlatformIntro() {
  const stats = [
    { value: 5, suffix: "", label: "Guided Investigations" },
    { value: 100, suffix: "%", label: "Safe Simulation" },
    { value: 0, suffix: "", label: "Real Systems Touched" },
    { value: 3, suffix: "", label: "Difficulty Tiers" },
  ];
  return (
    <div className="border-y border-border/70 bg-surface/60">
      <Section className="!py-14">
        <Reveal className="mb-10 text-center">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-subtle">
            A cyber range built for learning, not liability
          </p>
        </Reveal>
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          {stats.map((s, i) => (
            <Reveal key={s.label} delay={i * 80} className="text-center">
              <div className="font-display text-4xl font-bold text-gradient">
                <CountUp value={s.value} suffix={s.suffix} />
              </div>
              <div className="mt-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                {s.label}
              </div>
            </Reveal>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* 03 — Why learn with TrinetLayer */
function WhyLearn() {
  const items: Array<{ icon: IconName; title: string; body: string; accent: string }> = [
    {
      icon: "target",
      title: "Learn by investigating",
      body: "Every lab is a case to crack. You don't memorise definitions — you find the flaw, gather evidence, and explain the fix.",
      accent: "cyan",
    },
    {
      icon: "shield",
      title: "Zero-risk environments",
      body: "Realistic simulations of vulnerable apps run entirely in your browser. Nothing you do can harm a real system.",
      accent: "success",
    },
    {
      icon: "gauge",
      title: "Progressive mastery",
      body: "Difficulty ramps deliberately from a weak login to raw HTTP analysis, so each skill builds on the last.",
      accent: "primary",
    },
    {
      icon: "eye",
      title: "Defender mindset",
      body: "Understand attacks well enough to stop them. Each completion ends with the secure approach a defender would take.",
      accent: "violet",
    },
  ];
  return (
    <Section>
      <SectionHeader
        eyebrow="Why Cyber Labs"
        title="Built to change how you think, not just what you know"
        description="Cybersecurity is a practice, not a syllabus. These labs train the instinct to spot, prove, and close vulnerabilities."
      />
      <div className="mt-14 grid gap-5 md:grid-cols-2">
        {items.map((it, i) => (
          <Reveal key={it.title} delay={i * 90}>
            <Tilt className="h-full">
            <GlowCard accent={it.accent} className="h-full p-7">
              <div className="flex items-start gap-4">
                <span
                  className={cx("grid h-12 w-12 shrink-0 place-items-center rounded-xl", accentText(it.accent))}
                  style={{ background: `color-mix(in srgb, ${accentHex(it.accent)} 12%, transparent)` }}
                >
                  <Icon name={it.icon} size={24} />
                </span>
                <div>
                  <h3 className="text-lg font-semibold text-foreground">{it.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{it.body}</p>
                </div>
              </div>
            </GlowCard>
            </Tilt>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}

/* 04 — Interactive learning path (timeline) */
function LearningPath() {
  const { navigate, labProgress } = useApp();
  const spine = useInView<HTMLDivElement>();
  return (
    <div className="relative overflow-hidden">
      <div className="absolute inset-0 bg-grid bg-grid-fade opacity-40" aria-hidden="true" />

      <Section className="relative">
        <SectionHeader
          align="center"
          eyebrow="Learning Path"
          title="One continuous investigation trail"
          description="Each lab unlocks the next. Follow the trail from identity flaws all the way to the wire."
        />
        <div ref={spine.ref} className="relative mx-auto mt-16 max-w-3xl">
          {/* vertical spine (draws down on scroll) */}
          <div
            className="absolute left-[27px] top-2 bottom-2 w-px origin-top bg-gradient-to-b from-cyan/60 via-primary/40 to-violet/40 sm:left-1/2"
            style={{
              transform: `scaleY(${spine.inView ? 1 : 0})`,
              transition: "transform 1.2s cubic-bezier(0.65,0,0.35,1)",
            }}
          />
          <div className="space-y-8">
            {LABS.map((lab, i) => {
              const p = labProgress(lab.id);
              const left = i % 2 === 0;
              return (
                <Reveal key={lab.id} delay={i * 70}>
                  <div className={cx("relative flex items-center gap-6 sm:justify-center")}>
                    <div className={cx("hidden flex-1 sm:block", left ? "order-1 text-right" : "order-3")} />
                    <div className="relative z-10 order-2 grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-card ring-1 ring-border">
                      <span
                        className={cx("font-display text-lg font-bold", accentText(lab.accent))}
                      >
                        {String(lab.number).padStart(2, "0")}
                      </span>
                      {p.status === "completed" && (
                        <span className="absolute -right-1 -top-1 grid h-5 w-5 place-items-center rounded-full bg-success text-background">
                          <Icon name="check" size={12} strokeWidth={3} />
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => p.status !== "locked" && navigate({ name: "lab", labId: lab.id })}
                      disabled={p.status === "locked"}
                      className={cx(
                        "order-3 flex-1 rounded-xl border border-border bg-card/70 p-4 text-left transition-all sm:max-w-xs",
                        left ? "sm:order-3" : "sm:order-1 sm:text-right",
                        p.status !== "locked" && "hover:border-cyan/40 hover:bg-card",
                        p.status === "locked" && "opacity-60",
                      )}
                    >
                      <div className="font-mono text-[10px] uppercase tracking-widest text-subtle">
                        {lab.category} · {lab.difficulty}
                      </div>
                      <div className="mt-1 font-semibold text-foreground">{lab.codename}</div>
                      <div className="mt-0.5 text-sm text-muted-foreground">{lab.title}</div>
                    </button>
                  </div>
                </Reveal>
              );
            })}
          </div>
        </div>
      </Section>
    </div>
  );
}

/* 05 — Five labs */
function FiveLabs() {
  const { navigate } = useApp();
  return (
    <Section>
      <div className="flex flex-wrap items-end justify-between gap-6">
        <SectionHeader
          eyebrow="The Labs"
          title="Five investigations, one defender"
          description="Each lab is a self-contained case with a mission, simulated target, hints, and an evidence trail."
        />
        <PremiumButton variant="outline" iconRight="arrow-right" onClick={() => navigate({ name: "labs" })}>
          View all labs
        </PremiumButton>
      </div>
      <div className="mt-14 grid gap-5 lg:grid-cols-2">
        {LABS.map((lab, i) => (
          <Reveal key={lab.id} delay={i * 60}>
            <Tilt max={4}>
              <LabCard lab={lab} />
            </Tilt>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}

/* 06 — Skill matrix */
function SkillMatrix() {
  return (
    <div className="border-y border-border/70 bg-surface/60">
      <Section>
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <Reveal>
            <SectionHeader
              eyebrow="Skill Matrix"
              title="Watch your capability take shape"
              description="Every completed investigation strengthens a defensive domain. Your skill matrix fills in as you progress — a live map of what you've mastered."
            />
            <div className="mt-8 space-y-3">
              {[
                "Identity & authentication",
                "Access control & authorization",
                "Injection & input handling",
                "Configuration & hardening",
                "Protocol & traffic analysis",
              ].map((s) => (
                <div key={s} className="flex items-center gap-3 text-sm text-muted-foreground">
                  <span className="grid h-6 w-6 place-items-center rounded-md bg-cyan/10 text-cyan">
                    <Icon name="check" size={14} strokeWidth={2.4} />
                  </span>
                  {s}
                </div>
              ))}
            </div>
          </Reveal>
          <Reveal delay={120}>
            <div className="rounded-2xl bg-card hairline p-6">
              <SkillRadar size={340} />
            </div>
          </Reveal>
        </div>
      </Section>
    </div>
  );
}

/* 07 — How the lab system works */
function HowItWorks() {
  const steps: Array<{ icon: IconName; title: string; body: string }> = [
    { icon: "compass", title: "Read the mission", body: "Each lab briefs you on the target and objective — what to look for and why it matters." },
    { icon: "search", title: "Investigate the target", body: "Interact with a simulated app: a browser, a form, a config file, or a raw HTTP capture." },
    { icon: "book", title: "Log your evidence", body: "Record observations as evidence cards that build toward your investigation summary." },
    { icon: "check-circle", title: "Prove the finding", body: "Name the vulnerability. A correct answer completes the case and scores your work." },
  ];
  return (
    <Section>
      <SectionHeader
        align="center"
        eyebrow="How It Works"
        title="A repeatable investigation loop"
        description="The same four-step rhythm powers every lab, so you can focus on the security, not the interface."
      />
      <div className="mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
        {steps.map((s, i) => (
          <Reveal key={s.title} delay={i * 80}>
            <div className="relative h-full rounded-2xl bg-card hairline p-6">

              <span className="grid h-11 w-11 place-items-center rounded-xl bg-cyan/10 text-cyan">
                <Icon name={s.icon} size={22} />
              </span>
              <h3 className="mt-4 font-semibold text-foreground">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}

/* 08 — Progress experience */
function ProgressExperience() {
  const { navigate } = useApp();
  return (
    <Section>
      <div className="grid items-center gap-12 lg:grid-cols-[0.9fr_1.1fr]">
        <Reveal>
          <div className="relative rounded-2xl bg-gradient-to-br from-card to-surface hairline p-8">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-mono text-[11px] uppercase tracking-widest text-subtle">
                  Overall Progress
                </div>
                <div className="mt-1 text-sm text-muted-foreground">Keep the streak going</div>
              </div>
              <Icon name="activity" size={20} className="text-cyan" />
            </div>
            <div className="mt-6 flex items-center gap-8">
              <ProgressRing value={40} size={140} label="40%" sublabel="2 / 5 labs" animate={false} />
              <div className="space-y-3">
                {[
                  { label: "Score", value: "220" },
                  { label: "Achievements", value: "3" },
                  { label: "Streak", value: "2 labs" },
                ].map((m) => (
                  <div key={m.label}>
                    <div className="font-display text-xl font-bold text-foreground">{m.value}</div>
                    <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                      {m.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <SectionHeader
            eyebrow="Progress Experience"
            title="Your command center tracks every move"
            description="A live dashboard captures scores, achievements, your skill radar, and the next recommended lab — so you always know where to go next."
          />
          <PremiumButton className="mt-8" iconRight="arrow-right" onClick={() => navigate({ name: "dashboard" })}>
            Open your dashboard
          </PremiumButton>
        </Reveal>
      </div>
    </Section>
  );
}

/* 09 — Security simulation model */
function SimulationModel() {
  return (
    <div className="border-y border-border/70 bg-surface/60">
      <Section>
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <Reveal>
            <SectionHeader
              eyebrow="Simulation Model"
              title="Real vulnerabilities. Zero real risk."
              description="Every target is a faithful simulation running locally. You practise genuine attack techniques against apps designed to be broken — never against live systems."
            />
          </Reveal>
          <Reveal delay={120}>
            <div className="rounded-2xl bg-background hairline p-1">
              <div className="flex items-center gap-1.5 border-b border-border px-4 py-3">
                <span className="h-2.5 w-2.5 rounded-full bg-danger/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-warning/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-success/70" />
                <span className="ml-3 font-mono text-[11px] text-muted-foreground">
                  simulation://sandbox
                </span>
                <span className="ml-auto inline-flex items-center gap-1.5 rounded-md bg-success/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-success">
                  <Icon name="shield" size={11} /> Safe
                </span>
              </div>
              <div className="space-y-1.5 p-5 font-mono text-xs leading-relaxed">
                <div className="text-muted-foreground">$ launch lab --id auth --mode simulate</div>
                <div className="text-success">✓ sandbox provisioned (in-memory)</div>
                <div className="text-success">✓ target: vulnerable-portal</div>
                <div className="text-cyan">→ isolation: browser-only, no network egress</div>
                <div className="text-muted-foreground">$ status</div>
                <div className="text-foreground">READY · no real systems in scope</div>
              </div>
            </div>
          </Reveal>
        </div>
      </Section>
    </div>
  );
}

/* 10 — Student journey */
function StudentJourney() {
  const phases = [
    { tag: "Day 1", title: "First finding", body: "Crack the weak login and log your first piece of evidence." },
    { tag: "Week 1", title: "Building instinct", body: "Move through access control and injection — patterns start to click." },
    { tag: "Week 2", title: "Reading the wire", body: "Analyse raw HTTP and reason about headers like a defender." },
    { tag: "Ongoing", title: "Sharpening", body: "Replay labs hint-free to raise scores and fill the skill matrix." },
  ];
  return (
    <Section>
      <SectionHeader
        eyebrow="Student Journey"
        title="From first login flaw to protocol fluency"
        description="A realistic arc of how learners grow through the path."
      />
      <div className="mt-14 grid gap-4 md:grid-cols-4">
        {phases.map((p, i) => (
          <Reveal key={p.tag} delay={i * 80}>
            <div className="h-full rounded-2xl bg-card hairline p-6">
              <div className="inline-block rounded-md bg-cyan/10 px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-cyan">
                {p.tag}
              </div>
              <h3 className="mt-4 font-semibold text-foreground">{p.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{p.body}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}

/* 11 — FAQ */
const FAQS: Array<{ q: string; a: string }> = [
  {
    q: "Is any of this happening against real systems?",
    a: "No. Every target is a fictional app that runs entirely in your browser. Cyber Labs never contacts real websites, servers, accounts, or IP addresses — the techniques are real, the targets are not.",
  },
  {
    q: "Do I need to install any external tools or API keys?",
    a: "No. Everything runs directly in your browser. Target simulations, hints, scoring, and skill profiling are computed entirely client-side with zero setup and zero dependencies.",
  },
  {
    q: "Do I need prior security experience?",
    a: "No. The path starts at a weak login and ramps deliberately. Each lab briefs the concept first, offers tiered hints, and ends by explaining the defender's fix.",
  },
  {
    q: "Is my progress saved?",
    a: "Yes — scores, evidence, achievements, and completion are stored locally in your browser, so you can close the tab and pick up where you left off. Resetting progress from the dashboard clears it.",
  },
  {
    q: "Does it work on mobile?",
    a: "Yes. Every page is responsive and the lab workspace collapses to a stacked layout on small screens. The immersive hero degrades gracefully and respects reduced-motion settings.",
  },
  {
    q: "Is it legal to practise these techniques here?",
    a: "Within these labs, absolutely — that's what they're for. Applying the same techniques to systems you don't own or have explicit permission to test is illegal. This platform exists to teach you to defend.",
  },
];

function Faq() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <Section id="faq">
      <SectionHeader
        align="center"
        eyebrow="FAQ"
        title="Questions, answered"
        description="The essentials about how the range works and how it keeps you — and everyone else — safe."
      />
      <div className="mx-auto mt-12 max-w-3xl space-y-3">
        {FAQS.map((item, i) => {
          const isOpen = open === i;
          return (
            <Reveal key={item.q} delay={i * 50}>
              <div
                className={cx(
                  "overflow-hidden rounded-2xl border bg-card transition-colors",
                  isOpen ? "border-cyan/30" : "border-border",
                )}
              >
                <button
                  onClick={() => setOpen(isOpen ? null : i)}
                  aria-expanded={isOpen}
                  aria-controls={`faq-panel-${i}`}
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                >
                  <span className="font-medium text-foreground">{item.q}</span>
                  <span
                    className={cx(
                      "grid h-7 w-7 shrink-0 place-items-center rounded-lg text-cyan transition-transform duration-300",
                      isOpen ? "rotate-180 bg-cyan/10" : "bg-muted/60",
                    )}
                  >
                    <Icon name="chevron-down" size={16} />
                  </span>
                </button>
                <div
                  id={`faq-panel-${i}`}
                  className="grid transition-all duration-300"
                  style={{ gridTemplateRows: isOpen ? "1fr" : "0fr" }}
                >
                  <div className="overflow-hidden">
                    <p className="px-5 pb-5 text-sm leading-relaxed text-muted-foreground">
                      {item.a}
                    </p>
                  </div>
                </div>
              </div>
            </Reveal>
          );
        })}
      </div>
    </Section>
  );
}

/* 12 — CTA */
function CallToAction() {
  const { navigate } = useApp();
  return (
    <Section>
      <Reveal>
        <div className="relative overflow-hidden rounded-3xl border border-cyan/20 bg-gradient-to-br from-primary/15 via-card to-violet/10 p-10 text-center sm:p-16">
          <div className="absolute inset-0 bg-grid opacity-30" aria-hidden="true" />
          <div
            className="absolute left-1/2 top-0 h-64 w-96 -translate-x-1/2 rounded-full opacity-60 blur-3xl"
            style={{ background: "radial-gradient(closest-side, rgba(34,211,238,0.35), transparent)" }}
            aria-hidden="true"
          />
          <div className="relative">
            <h2 className="mx-auto max-w-2xl font-display text-3xl font-bold leading-tight sm:text-5xl">
              Your first investigation is one click away
            </h2>
            <p className="mx-auto mt-5 max-w-xl text-muted-foreground">
              Start with the weak front door. No setup, no risk — just you, a target, and the
              instinct you're about to build.
            </p>
            <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
              <PremiumButton size="lg" iconRight="arrow-right" onClick={() => navigate({ name: "lab", labId: "auth" })}>
                Start Your First Lab
              </PremiumButton>
              <PremiumButton size="lg" variant="outline" icon="layers" onClick={() => navigate({ name: "labs" })}>
                Browse all labs
              </PremiumButton>
            </div>
          </div>
        </div>
      </Reveal>
    </Section>
  );
}

export function Home() {
  return (
    <div>
      <Hero />
      <PlatformIntro />
      <WhyLearn />
      <LearningPath />
      <FiveLabs />
      <SkillMatrix />
      <HowItWorks />
      <ProgressExperience />
      <SimulationModel />
      <StudentJourney />
      <Faq />
      <CallToAction />
    </div>
  );
}
