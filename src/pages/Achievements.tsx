import { useApp } from "../context/AppContext";
import { ACHIEVEMENTS } from "../lib/achievements";
import { Icon } from "../components/ui/Icon";
import type { IconName } from "../components/ui/Icon";
import {
  PremiumButton,
  ProgressBar,
  Reveal,
  SectionHeader,
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

export function Achievements() {
  const { state, navigate } = useApp();
  const unlockedCount = state.achievements.length;
  const total = ACHIEVEMENTS.length;
  const pct = Math.round((unlockedCount / total) * 100);

  return (
    <div className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <SectionHeader
        eyebrow="Achievements"
        title="Marks of a sharpening defender"
        description="Badges recognise how you investigate — solving hint-free, striking on the first attempt, and closing every case. They're earned automatically as you progress."
      />

      <Reveal className="mt-10">
        <div className="rounded-2xl bg-gradient-to-br from-card to-surface hairline p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              <Icon name="award" size={14} className="text-cyan" /> Unlocked
            </div>
            <span className="font-display text-lg font-bold text-foreground">
              {unlockedCount} <span className="text-subtle">/ {total}</span>
            </span>
          </div>
          <ProgressBar value={pct} className="mt-3" />
        </div>
      </Reveal>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ACHIEVEMENTS.map((a, i) => {
          const unlocked = state.achievements.includes(a.id);
          return (
            <Reveal key={a.id} delay={i * 60}>
              <div
                className={cx(
                  "flex h-full items-start gap-4 rounded-2xl border p-5 transition-colors",
                  unlocked ? "border-cyan/30 bg-cyan/5" : "border-border bg-muted/20",
                )}
              >
                <span
                  className={cx(
                    "grid h-12 w-12 shrink-0 place-items-center rounded-xl",
                    unlocked ? "bg-cyan/15 text-cyan" : "bg-muted text-subtle",
                  )}
                >
                  <Icon name={unlocked ? ACH_ICON[a.icon] : "lock"} size={22} />
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-foreground">{a.title}</h3>
                    {unlocked && (
                      <span className="rounded-full bg-success/10 px-2 py-0.5 font-mono text-[9px] uppercase tracking-widest text-success">
                        Earned
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                    {a.description}
                  </p>
                </div>
              </div>
            </Reveal>
          );
        })}
      </div>

      {unlockedCount < total && (
        <Reveal className="mt-10">
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-card hairline p-6">
            <p className="text-sm text-muted-foreground">
              Keep investigating — the fastest way to earn badges is to close a case hint-free.
            </p>
            <PremiumButton iconRight="arrow-right" onClick={() => navigate({ name: "labs" })}>
              Go to labs
            </PremiumButton>
          </div>
        </Reveal>
      )}
    </div>
  );
}
