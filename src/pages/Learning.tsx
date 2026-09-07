import { useApp } from "../context/AppContext";
import { LABS } from "../lib/labs";
import { Icon } from "../components/ui/Icon";
import {
  Chip,
  DifficultyBadge,
  PremiumButton,
  Reveal,
  SectionHeader,
  StatusBadge,
  accentHex,
  accentText,
  cx,
} from "../components/ui/primitives";

export function Learning() {
  const { navigate, labProgress } = useApp();

  return (
    <div className="mx-auto max-w-5xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <SectionHeader
        eyebrow="Learning Path"
        title="The defender's curriculum"
        description="A guided arc through five domains of application security. Follow it in order — each concept builds on the one before."
      />

      <div className="relative mt-14">
        <div className="absolute bottom-4 left-6 top-4 w-px bg-gradient-to-b from-cyan/60 via-primary/40 to-violet/40" />
        <div className="space-y-6">
          {LABS.map((lab, i) => {
            const p = labProgress(lab.id);
            return (
              <Reveal key={lab.id} delay={i * 70}>
                <div className="relative flex gap-6">
                  <div className="relative z-10 grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-card ring-1 ring-border">
                    <span className={cx("font-display font-bold", accentText(lab.accent))}>
                      {String(lab.number).padStart(2, "0")}
                    </span>
                  </div>
                  <div className="flex-1 rounded-2xl border border-border bg-card p-6">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="font-mono text-[11px] uppercase tracking-widest text-subtle">
                          {lab.category}
                        </div>
                        <h3 className="mt-0.5 text-lg font-semibold text-foreground">
                          {lab.codename} — {lab.title}
                        </h3>
                      </div>
                      <StatusBadge status={p.status} />
                    </div>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{lab.summary}</p>
                    <div className="mt-4 flex flex-wrap items-center gap-2">
                      <DifficultyBadge level={lab.difficulty} />
                      <Chip icon="clock">{lab.estMinutes} min</Chip>
                      {lab.skills.map((s) => (
                        <Chip key={s}>{s}</Chip>
                      ))}
                    </div>
                    <div className="mt-5 rounded-xl bg-muted/40 p-4">
                      <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
                        <Icon name="lightbulb" size={13} /> What you'll learn
                      </div>
                      <ul className="mt-2 space-y-1.5">
                        {lab.objectives.map((o) => (
                          <li key={o} className="flex items-start gap-2 text-sm text-muted-foreground">
                            <Icon name="chevron-right" size={14} className="mt-0.5 shrink-0 text-subtle" />
                            {o}
                          </li>
                        ))}
                      </ul>
                    </div>
                    {p.status !== "locked" && (
                      <PremiumButton
                        className="mt-5"
                        size="sm"
                        variant="outline"
                        iconRight="arrow-right"
                        onClick={() => navigate({ name: "lab", labId: lab.id })}
                      >
                        {p.status === "completed" ? "Review lab" : "Open lab"}
                      </PremiumButton>
                    )}
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </div>
  );
}
