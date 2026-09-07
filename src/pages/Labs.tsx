import { useApp } from "../context/AppContext";
import { LABS } from "../lib/labs";
import { LabCard } from "../components/LabCard";
import { Icon } from "../components/ui/Icon";
import {
  MetricCard,
  ProgressBar,
  Reveal,
  SectionHeader,
  cx,
} from "../components/ui/primitives";

export function Labs() {
  const { completedCount, totalScore, state } = useApp();
  const inProgress = Object.values(state.labs).filter((l) => l.status === "in-progress").length;
  const pct = Math.round((completedCount / LABS.length) * 100);

  return (
    <div className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <div className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-card to-surface p-8 sm:p-10">
        <div className="absolute inset-0 bg-grid bg-grid-fade opacity-40" aria-hidden="true" />
        <div className="relative flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan/25 bg-cyan/5 px-3 py-1 font-mono text-[11px] uppercase tracking-[0.25em] text-cyan">
              <Icon name="layers" size={13} /> Investigation Trail
            </div>
            <h1 className="mt-4 font-display text-3xl font-bold sm:text-4xl">The Five Labs</h1>
            <p className="mt-3 text-muted-foreground">
              Work the trail top to bottom. Each case unlocks the next as you prove your findings.
            </p>
            <div className="mt-5 max-w-md">
              <div className="mb-1.5 flex justify-between font-mono text-[11px] text-muted-foreground">
                <span>Path completion</span>
                <span>{pct}%</span>
              </div>
              <ProgressBar value={pct} />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <MetricCard icon="check-circle" accent="success" value={`${completedCount}/5`} label="Complete" />
            <MetricCard icon="activity" accent="warning" value={inProgress} label="Active" />
            <MetricCard icon="bar-chart" accent="cyan" value={totalScore} label="Score" />
          </div>
        </div>
      </div>

      <SectionHeader
        className="mt-16"
        eyebrow="Select a lab"
        title="Choose your next investigation"
      />

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        {LABS.map((lab, i) => (
          <Reveal key={lab.id} delay={i * 60} className={cx(i === LABS.length - 1 && "lg:col-span-2 lg:max-w-[calc(50%-0.625rem)]")}>
            <LabCard lab={lab} />
          </Reveal>
        ))}
      </div>
    </div>
  );
}
