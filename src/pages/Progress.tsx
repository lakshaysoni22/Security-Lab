import { useApp } from "../context/AppContext";
import { LABS } from "../lib/labs";
import { LearningEngine, RecommendationEngine } from "../lib/engine";
import { SkillRadar } from "../components/SkillRadar";
import { Icon } from "../components/ui/Icon";
import type { IconName } from "../components/ui/Icon";
import {
  CountUp,
  DifficultyBadge,
  GlowCard,
  PremiumButton,
  ProgressBar,
  ProgressRing,
  Reveal,
  SectionHeader,
  StatusBadge,
  accentText,
  cx,
} from "../components/ui/primitives";

function fmtTime(ms: number) {
  const m = Math.round(ms / 60000);
  if (m < 1) return "<1m";
  if (m < 60) return `${m}m`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

export function Progress() {
  const { state, navigate, totalScore, completedCount } = useApp();
  const pct = Math.round((completedCount / LABS.length) * 100);
  const totalTime = Object.values(state.labs).reduce((a, l) => a + l.timeSpentMs, 0);
  const totalHints = Object.values(state.labs).reduce((a, l) => a + l.hintsUsed, 0);
  const totalAttempts = Object.values(state.labs).reduce((a, l) => a + l.attempts, 0);
  const summary = LearningEngine.summary(state);
  const weakest = LearningEngine.weakestSkill(state);
  const strengths = LearningEngine.strengths(state);
  const weaknesses = LearningEngine.weaknesses(state);
  const nextConcept = LearningEngine.recommendedConcept(state);
  const nextLab = RecommendationEngine.nextLab(state);

  const metrics: Array<{ icon: IconName; label: string; value: number | string; accent: string }> = [
    { icon: "bar-chart", label: "Total score", value: totalScore, accent: "cyan" },
    { icon: "check-circle", label: "Labs closed", value: completedCount, accent: "success" },
    { icon: "lightbulb", label: "Hints used", value: totalHints, accent: "warning" },
    { icon: "target", label: "Attempts", value: totalAttempts, accent: "primary" },
    { icon: "clock", label: "Time invested", value: fmtTime(totalTime), accent: "violet" },
    { icon: "award", label: "Achievements", value: state.achievements.length, accent: "cyan" },
  ];

  return (
    <div className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <SectionHeader
        eyebrow="Progress"
        title="Every move, measured"
        description={summary}
      />

      <div className="mt-10 grid gap-5 lg:grid-cols-3">
        {/* overall ring */}
        <Reveal className="lg:col-span-1">
          <div className="flex h-full flex-col items-center justify-center rounded-2xl bg-gradient-to-br from-card to-surface hairline p-8">
            <ProgressRing value={pct} size={190} label={`${pct}%`} sublabel={`${completedCount} / ${LABS.length} labs`} />
            {nextLab && (
              <PremiumButton
                className="mt-6"
                variant="outline"
                iconRight="arrow-right"
                onClick={() => navigate({ name: "lab", labId: nextLab.id })}
              >
                {RecommendationEngine.reasonFor(state, nextLab)}
              </PremiumButton>
            )}
          </div>
        </Reveal>

        {/* metrics */}
        <Reveal delay={80} className="lg:col-span-2">
          <div className="grid h-full grid-cols-2 gap-4 sm:grid-cols-3">
            {metrics.map((m) => (
              <div key={m.label} className="rounded-2xl bg-card hairline p-5">
                <div className={cx("flex items-center gap-1.5", accentText(m.accent))}>
                  <Icon name={m.icon} size={15} />
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    {m.label}
                  </span>
                </div>
                <div className="mt-2 font-display text-2xl font-bold text-foreground">
                  {typeof m.value === "number" ? <CountUp value={m.value} /> : m.value}
                </div>
              </div>
            ))}
          </div>
        </Reveal>
      </div>

      {/* per-lab breakdown + radar */}
      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <Reveal className="lg:col-span-2">
          <div className="h-full rounded-2xl bg-card hairline p-6">
            <div className="mb-5 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              <Icon name="route" size={14} className="text-cyan" /> Lab breakdown
            </div>
            <div className="space-y-3">
              {LABS.map((lab) => {
                const p = state.labs[lab.id];
                const status = p?.status ?? "locked";
                const val = status === "completed" ? 100 : status === "in-progress" ? 50 : 0;
                return (
                  <button
                    key={lab.id}
                    onClick={() => status !== "locked" && navigate({ name: "lab", labId: lab.id })}
                    disabled={status === "locked"}
                    className="flex w-full flex-wrap items-center gap-4 rounded-xl px-3 py-3 text-left transition-colors hover:bg-muted/40 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <span className={cx("w-8 font-display text-sm font-bold", accentText(lab.accent))}>
                      {String(lab.number).padStart(2, "0")}
                    </span>
                    <span className="min-w-[8rem] flex-1">
                      <span className="text-sm font-medium text-foreground">{lab.codename}</span>
                      <ProgressBar value={val} accent={lab.accent} className="mt-1.5" />
                    </span>
                    <span className="hidden font-mono text-[11px] text-subtle sm:inline">
                      {p?.score ?? 0} pts · {p?.hintsUsed ?? 0}h · {p?.attempts ?? 0}a
                    </span>
                    <DifficultyBadge level={lab.difficulty} />
                    <StatusBadge status={status} />
                  </button>
                );
              })}
            </div>
          </div>
        </Reveal>

        <Reveal delay={80} className="lg:col-span-1">
          <GlowCard className="h-full p-6">
            <div className="mb-2 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              <Icon name="target" size={14} className="text-cyan" /> Skill matrix
            </div>
            <SkillRadar size={280} />
            {weakest && completedCount < LABS.length && (
              <p className="mt-2 text-center text-sm text-muted-foreground">
                Focus next on <span className="font-semibold text-cyan">{weakest.key}</span>.
              </p>
            )}
          </GlowCard>
        </Reveal>
      </div>

      {/* learning analytics */}
      <Reveal className="mt-5">
        <div className="grid gap-5 rounded-2xl bg-card hairline p-6 sm:grid-cols-3">
          <div>
            <div className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-widest text-success">
              <Icon name="check-circle" size={14} /> Strengths
            </div>
            {strengths.length === 0 ? (
              <p className="mt-2 text-sm text-subtle">
                Complete a lab with a high score to build a strength.
              </p>
            ) : (
              <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                {strengths.map((s) => (
                  <li key={s.key}>{s.key}</li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <div className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-widest text-warning">
              <Icon name="target" size={14} /> Areas to develop
            </div>
            {weaknesses.length === 0 ? (
              <p className="mt-2 text-sm text-subtle">Every domain is at full mastery.</p>
            ) : (
              <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                {weaknesses.map((w) => (
                  <li key={w.key}>{w.key}</li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <div className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-widest text-cyan">
              <Icon name="route" size={14} /> Recommended next concept
            </div>
            {nextConcept ? (
              <button
                onClick={() => navigate({ name: "lab", labId: nextConcept.labId })}
                className="mt-2 text-left text-sm text-foreground hover:text-cyan"
              >
                <span className="font-semibold">{nextConcept.key}</span>
                <span className="block font-mono text-[11px] text-subtle">Open the lab →</span>
              </button>
            ) : (
              <p className="mt-2 text-sm text-subtle">All concepts covered.</p>
            )}
          </div>
        </div>
      </Reveal>
    </div>
  );
}
