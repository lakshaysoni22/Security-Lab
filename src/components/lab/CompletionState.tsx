import { useApp } from "../../context/AppContext";
import { LABS } from "../../lib/labs";
import type { Lab } from "../../lib/types";
import { Icon } from "../ui/Icon";
import type { IconName } from "../ui/Icon";
import { CountUp, PremiumButton, ProgressRing, cx } from "../ui/primitives";
import { Confetti } from "../fx/Confetti";
import { DrawCheck } from "../fx/DrawCheck";

function fmt(ms: number) {
  const m = Math.round(ms / 60000);
  return m < 1 ? "<1m" : `${m}m`;
}

export function CompletionState({ lab }: { lab: Lab }) {
  const { labProgress, navigate } = useApp();
  const p = labProgress(lab.id);
  const idx = LABS.findIndex((l) => l.id === lab.id);
  const next = LABS[idx + 1];
  // Base-100 model: the score is already a percentage; clamp for legacy saves.
  const scorePct = Math.min(100, p.score);
  const sp = p.stepProgress ?? {};
  const completedSteps = (lab.steps ?? []).filter((s) => sp[s.id]?.done);

  const insights: Array<{ icon: IconName; label: string; body: string; accent: string }> = [
    { icon: "search", label: "What you discovered", body: lab.outcome.discovered, accent: "cyan" },
    { icon: "alert", label: "Why it matters", body: lab.outcome.whyItMatters, accent: "warning" },
    { icon: "shield", label: "Secure approach", body: lab.outcome.secureApproach, accent: "success" },
    { icon: "route", label: "Next skill", body: lab.outcome.nextSkill, accent: "violet" },
  ];

  return (
    <div className="mx-auto max-w-3xl">
      <div className="animate-pop-in relative overflow-hidden rounded-3xl border border-success/30 bg-gradient-to-br from-success/10 via-card to-card p-8 text-center sm:p-10">
        <Confetti />
        <div className="relative mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-success/20 glow-cyan">
          <DrawCheck size={44} />
        </div>
        <div className="mt-4 font-mono text-xs uppercase tracking-[0.3em] text-success">
          Investigation Complete
        </div>
        <h2 className="mt-2 font-display text-3xl font-bold sm:text-4xl">{lab.title}</h2>
        <p className="mt-2 text-muted-foreground">You correctly identified the vulnerability.</p>

        <div className="mt-8 flex flex-col items-center gap-8 sm:flex-row sm:justify-center">
          <ProgressRing value={scorePct} size={150} accent="success" label={<CountUp value={p.score} />} sublabel="score" />
          <div className="grid grid-cols-3 gap-5">
            {[
              { icon: "target" as IconName, label: "Attempts", value: p.attempts },
              { icon: "lightbulb" as IconName, label: "Hints", value: p.hintsUsed },
              { icon: "clock" as IconName, label: "Time", value: fmt(p.timeSpentMs) },
            ].map((m) => (
              <div key={m.label}>
                <div className="mx-auto mb-1 grid h-9 w-9 place-items-center rounded-lg bg-muted text-cyan">
                  <Icon name={m.icon} size={16} />
                </div>
                <div className="font-display text-xl font-bold text-foreground">
                  {typeof m.value === "number" ? <CountUp value={m.value} /> : m.value}
                </div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  {m.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {(completedSteps.length > 0 || p.evidence.length > 0) && (
        <div className="mt-5 rounded-2xl border border-border bg-card p-6">
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
            <Icon name="search" size={14} /> Investigation summary
          </div>
          <div className="mt-4 grid gap-6 sm:grid-cols-2">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-subtle">
                Steps completed
              </div>
              <ol className="mt-2 space-y-1.5">
                {completedSteps.map((s) => (
                  <li key={s.id} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <Icon name="check" size={14} className="mt-0.5 shrink-0 text-success" />
                    {s.title}
                  </li>
                ))}
              </ol>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-subtle">
                Evidence logged ({p.evidence.length})
              </div>
              {p.evidence.length === 0 ? (
                <p className="mt-2 text-sm text-subtle">No evidence recorded this run.</p>
              ) : (
                <ul className="mt-2 space-y-1.5">
                  {p.evidence.map((e) => (
                    <li key={e.id} className="text-sm text-muted-foreground">
                      <span className="font-mono text-[10px] uppercase text-cyan">
                        {e.category}
                      </span>{" "}
                      — {e.observation}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {insights.map((it) => (
          <div key={it.label} className="rounded-2xl border border-border bg-card p-5">
            <div
              className={cx(
                "flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest",
                it.accent === "cyan" && "text-cyan",
                it.accent === "warning" && "text-warning",
                it.accent === "success" && "text-success",
                it.accent === "violet" && "text-violet",
              )}
            >
              <Icon name={it.icon} size={14} /> {it.label}
            </div>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{it.body}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
        {next ? (
          <PremiumButton
            size="lg"
            iconRight="arrow-right"
            onClick={() => navigate({ name: "lab", labId: next.id })}
          >
            Continue to Lab {String(next.number).padStart(2, "0")}
          </PremiumButton>
        ) : (
          <PremiumButton size="lg" iconRight="arrow-right" onClick={() => navigate({ name: "dashboard" })}>
            View your dashboard
          </PremiumButton>
        )}
        <PremiumButton size="lg" variant="outline" icon="layers" onClick={() => navigate({ name: "labs" })}>
          Back to labs
        </PremiumButton>
      </div>
    </div>
  );
}
