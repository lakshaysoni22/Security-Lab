import { useApp } from "../context/AppContext";
import { LABS } from "../lib/labs";
import { RecommendationEngine } from "../lib/engine";
import { ACHIEVEMENTS } from "../lib/achievements";
import { SkillRadar } from "../components/SkillRadar";
import { Icon } from "../components/ui/Icon";
import type { IconName } from "../components/ui/Icon";
import {
  Chip,
  CountUp,
  GlowCard,
  PremiumButton,
  ProgressBar,
  ProgressRing,
  Reveal,
  StatusBadge,
  accentText,
  cx,
} from "../components/ui/primitives";

const ACH_ICON: Record<string, IconName> = {
  flag: "flag",
  shield: "shield",
  zap: "zap",
  target: "target",
  crown: "crown",
  eye: "eye",
};

function Sparkline({ points }: { points: number[] }) {
  if (points.length < 2) return null;
  const w = 120;
  const h = 32;
  const max = Math.max(...points, 1);
  const min = Math.min(...points, 0);
  const span = max - min || 1;
  const step = w / (points.length - 1);
  const coords = points.map((p, i) => [i * step, h - ((p - min) / span) * (h - 6) - 3]);
  const d = coords.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const [lx, ly] = coords[coords.length - 1];
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
      <path d={`${d} L${w},${h} L0,${h} Z`} fill="rgba(34,211,238,0.10)" />
      <path d={d} fill="none" stroke="#22d3ee" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lx} cy={ly} r={2.6} fill="#a9f0ff" />
    </svg>
  );
}

function fmtTime(ms: number) {
  const m = Math.round(ms / 60000);
  if (m < 1) return "<1m";
  if (m < 60) return `${m}m`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

export function Dashboard() {
  const { state, navigate, totalScore, completedCount, reset } = useApp();
  const pct = Math.round((completedCount / LABS.length) * 100);

  const totalTime = Object.values(state.labs).reduce((a, l) => a + l.timeSpentMs, 0);
  const totalHints = Object.values(state.labs).reduce((a, l) => a + l.hintsUsed, 0);
  const totalAttempts = Object.values(state.labs).reduce((a, l) => a + l.attempts, 0);

  const nextLab = RecommendationEngine.nextLab(state);
  const nextReason = nextLab ? RecommendationEngine.reasonFor(state, nextLab) : "";

  // recent activity: completed labs sorted by completion time
  const recent = LABS.map((l) => ({ lab: l, p: state.labs[l.id] }))
    .filter((x) => x.p?.completedAt)
    .sort((a, b) => (b.p.completedAt ?? 0) - (a.p.completedAt ?? 0))
    .slice(0, 4);

  return (
    <div className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      {/* header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-cyan">
            Command Center
          </div>
          <h1 className="mt-2 font-display text-3xl font-bold sm:text-4xl">
            Welcome back, {state.learnerName}
          </h1>
          <p className="mt-2 text-muted-foreground">
            {completedCount === LABS.length
              ? "Every case closed. Replay a lab hint-free to push your score."
              : "Here's where your investigation stands."}
          </p>
        </div>
        <PremiumButton variant="ghost" size="sm" icon="trash" onClick={reset}>
          Reset progress
        </PremiumButton>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-3">
        {/* overall progress */}
        <Reveal className="lg:col-span-1">
          <div className="flex h-full flex-col items-center justify-center rounded-2xl bg-gradient-to-br from-card to-surface hairline p-8">
            <ProgressRing value={pct} size={190} label={`${pct}%`} sublabel={`${completedCount} / ${LABS.length} labs`} />
            <div className="mt-6 grid w-full grid-cols-3 gap-3 text-center">
              <div>
                <div className="font-display text-xl font-bold text-foreground">
                  <CountUp value={totalScore} />
                </div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Score</div>
              </div>
              <div>
                <div className="font-display text-xl font-bold text-foreground">
                  <CountUp value={state.achievements.length} />
                </div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Badges</div>
              </div>
              <div>
                <div className="font-display text-xl font-bold text-foreground">{fmtTime(totalTime)}</div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Time</div>
              </div>
            </div>
          </div>
        </Reveal>

        {/* recommended + learning path */}
        <Reveal delay={80} className="lg:col-span-2">
          <div className="flex h-full flex-col gap-5">
            {nextLab && (
              <GlowCard accent={nextLab.accent} className="p-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <div className="font-mono text-[11px] uppercase tracking-widest text-cyan">
                      Recommended next · {nextReason}
                    </div>
                    <h3 className="mt-1 text-xl font-semibold text-foreground">
                      Lab {String(nextLab.number).padStart(2, "0")} · {nextLab.title}
                    </h3>
                    <p className="mt-1 max-w-md text-sm text-muted-foreground">{nextLab.summary}</p>
                  </div>
                  <PremiumButton
                    iconRight="arrow-right"
                    onClick={() => navigate({ name: "lab", labId: nextLab.id })}
                  >
                    {state.labs[nextLab.id]?.status === "in-progress"
                      ? "Resume"
                      : state.labs[nextLab.id]?.status === "completed"
                        ? "Replay"
                        : "Start"}
                  </PremiumButton>
                </div>
              </GlowCard>
            )}

            <div className="rounded-2xl bg-card hairline p-6">
              <div className="mb-4 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                <Icon name="route" size={14} className="text-cyan" /> Learning path
              </div>
              <div className="space-y-3">
                {LABS.map((lab) => {
                  const p = state.labs[lab.id];
                  const val = p?.status === "completed" ? 100 : p?.status === "in-progress" ? 50 : 0;
                  return (
                    <button
                      key={lab.id}
                      onClick={() => p?.status !== "locked" && navigate({ name: "lab", labId: lab.id })}
                      disabled={p?.status === "locked"}
                      className="flex w-full items-center gap-4 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-muted/40 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <span className={cx("w-8 font-display text-sm font-bold", accentText(lab.accent))}>
                        {String(lab.number).padStart(2, "0")}
                      </span>
                      <span className="flex-1">
                        <span className="text-sm font-medium text-foreground">{lab.codename}</span>
                        <ProgressBar value={val} accent={lab.accent} className="mt-1.5" />
                      </span>
                      <StatusBadge status={p?.status ?? "locked"} />
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </Reveal>
      </div>

      {/* skill radar + performance + recent */}
      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <Reveal className="lg:col-span-1">
          <div className="h-full rounded-2xl bg-card hairline p-6">
            <div className="mb-2 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              <Icon name="target" size={14} className="text-cyan" /> Skill matrix
            </div>
            <SkillRadar size={280} />
          </div>
        </Reveal>

        <Reveal delay={80} className="lg:col-span-1">
          <div className="h-full rounded-2xl bg-card hairline p-6">
            <div className="mb-4 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              <Icon name="gauge" size={14} className="text-cyan" /> Performance
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { icon: "bar-chart" as IconName, label: "Total score", value: totalScore, accent: "cyan" },
                { icon: "lightbulb" as IconName, label: "Hints used", value: totalHints, accent: "warning" },
                { icon: "target" as IconName, label: "Attempts", value: totalAttempts, accent: "primary" },
                { icon: "clock" as IconName, label: "Time", value: fmtTime(totalTime), accent: "violet" },
              ].map((m) => (
                <div key={m.label} className="rounded-xl bg-muted/40 p-4">
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
          </div>
        </Reveal>

        <Reveal delay={160} className="lg:col-span-1">
          <div className="h-full rounded-2xl bg-card hairline p-6">
            <div className="mb-4 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              <Icon name="activity" size={14} className="text-cyan" /> Recent activity
              {recent.length >= 2 && (
                <span className="ml-auto">
                  <Sparkline points={[...recent].reverse().map((r) => r.p.score)} />
                </span>
              )}
            </div>
            {recent.length === 0 ? (
              <div className="grid h-40 place-items-center text-center text-sm text-muted-foreground">
                <div>
                  <Icon name="search" size={24} className="mx-auto mb-2 text-subtle" />
                  No completed labs yet.
                  <br />
                  Your findings will appear here.
                </div>
              </div>
            ) : (
              <ul className="space-y-3">
                {recent.map(({ lab, p }) => (
                  <li key={lab.id} className="flex items-center gap-3">
                    <span className="grid h-9 w-9 place-items-center rounded-lg bg-success/10 text-success">
                      <Icon name="check-circle" size={16} />
                    </span>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-foreground">{lab.title}</div>
                      <div className="font-mono text-[11px] text-muted-foreground">
                        Solved · score {p.score}
                      </div>
                    </div>
                    <Chip>{p.hintsUsed}h</Chip>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Reveal>
      </div>

      {/* achievements */}
      <Reveal className="mt-5">
        <div className="rounded-2xl bg-card hairline p-6">
          <div className="mb-5 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
            <Icon name="award" size={14} className="text-cyan" /> Achievements
            <span className="ml-auto text-subtle">
              {state.achievements.length} / {ACHIEVEMENTS.length}
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {ACHIEVEMENTS.map((a) => {
              const unlocked = state.achievements.includes(a.id);
              return (
                <div
                  key={a.id}
                  className={cx(
                    "flex items-center gap-3 rounded-xl border p-4 transition-colors",
                    unlocked
                      ? "border-cyan/30 bg-cyan/5"
                      : "border-border bg-muted/20 opacity-60",
                  )}
                >
                  <span
                    className={cx(
                      "grid h-11 w-11 shrink-0 place-items-center rounded-xl",
                      unlocked ? "bg-cyan/15 text-cyan" : "bg-muted text-subtle",
                    )}
                  >
                    <Icon name={unlocked ? ACH_ICON[a.icon] : "lock"} size={20} />
                  </span>
                  <div>
                    <div className="text-sm font-semibold text-foreground">{a.title}</div>
                    <div className="text-xs text-muted-foreground">{a.description}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Reveal>
    </div>
  );
}
