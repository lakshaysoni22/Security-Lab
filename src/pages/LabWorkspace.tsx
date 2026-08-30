import { useEffect, useMemo, useRef, useState } from "react";
import { useApp } from "../context/AppContext";
import { FINAL_STEP_ID, getLab } from "../lib/labs";
import type { ChallengeOption, Lab, LabStepKind } from "../lib/types";
import { Simulation } from "../components/lab/Simulation";
import { HintPanel } from "../components/lab/HintPanel";
import { EvidencePanel } from "../components/lab/EvidencePanel";
import { CompletionState } from "../components/lab/CompletionState";
import { Icon } from "../components/ui/Icon";
import {
  DifficultyBadge,
  PremiumButton,
  ProgressBar,
  cx,
} from "../components/ui/primitives";

interface Stage {
  id: string;
  kind: LabStepKind;
  title: string;
  prompt: string;
  requires?: string[];
  question?: string;
  options?: ChallengeOption[];
  answer?: string;
  wrongFeedback?: string;
  explanation?: string;
}

function buildStages(lab: Lab): Stage[] {
  const stages: Stage[] = (lab.steps ?? []).map((s) => ({ ...s }));
  if (lab.finalAssessment) {
    stages.push({
      id: FINAL_STEP_ID,
      kind: "decide",
      title: "Final assessment",
      prompt: lab.finalAssessment.question,
      question: lab.finalAssessment.question,
      options: lab.finalAssessment.options,
      answer: lab.finalAssessment.answer,
      wrongFeedback: lab.finalAssessment.wrongFeedback,
      explanation: lab.finalAssessment.explanation,
    });
  }
  return stages;
}

export function LabWorkspace({ labId }: { labId: string }) {
  const {
    navigate,
    startLab,
    labProgress,
    addTime,
    addInteraction,
    markStepDone,
    submitStep,
  } = useApp();
  const lab = getLab(labId);
  const [choiceByStep, setChoiceByStep] = useState<Record<string, string>>({});
  const [wrongStep, setWrongStep] = useState<string | null>(null);
  const [shake, setShake] = useState(false);
  const startRef = useRef<number>(Date.now());

  useEffect(() => {
    if (!lab) return;
    startLab(lab.id);
    startRef.current = Date.now();
    return () => {
      addTime(lab.id, Date.now() - startRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labId]);

  const stages = useMemo(() => (lab ? buildStages(lab) : []), [lab]);

  if (!lab) {
    return (
      <div className="grid min-h-screen place-items-center px-6 text-center">
        <div>
          <p className="text-muted-foreground">Lab not found.</p>
          <PremiumButton className="mt-4" onClick={() => navigate({ name: "labs" })}>
            Back to labs
          </PremiumButton>
        </div>
      </div>
    );
  }

  const p = labProgress(lab.id);
  const solved = p.status === "completed";
  const sp = p.stepProgress ?? {};

  const doneCount = stages.filter((s) => sp[s.id]?.done).length;
  const activeIndex = stages.findIndex((s) => !sp[s.id]?.done);
  const pct = stages.length ? Math.round((doneCount / stages.length) * 100) : 0;

  // Route a sim interaction to whichever observe/probe step requires that tag.
  const handleInteraction = (tag: string) => {
    stages.forEach((s) => {
      if (s.kind !== "decide" && s.requires?.includes(tag)) {
        addInteraction(lab.id, s.id, tag);
      }
    });
  };

  const submitDecide = (stage: Stage) => {
    const choice = choiceByStep[stage.id];
    if (!choice) return;
    addTime(lab.id, Date.now() - startRef.current);
    startRef.current = Date.now();
    const ok = submitStep(lab.id, stage.id, choice);
    if (!ok) {
      setWrongStep(stage.id);
      setShake(true);
      setTimeout(() => setShake(false), 500);
    } else {
      setWrongStep(null);
    }
  };

  return (
    <div className="min-h-screen pt-16">
      {/* top bar */}
      <div className="sticky top-16 z-30 border-b border-border/80 glass">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center gap-x-4 gap-y-2 px-5 py-3 sm:px-8">
          <button
            onClick={() => navigate({ name: "labs" })}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
          >
            <Icon name="chevron-right" size={16} className="rotate-180" /> Labs
          </button>
          <span className="hidden text-subtle sm:inline">/</span>
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-cyan">
              LAB {String(lab.number).padStart(2, "0")}
            </span>
            <h1 className="text-base font-semibold text-foreground sm:text-lg">{lab.title}</h1>
          </div>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <DifficultyBadge level={lab.difficulty} />
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 font-mono text-[11px] text-muted-foreground">
              <Icon name="clock" size={12} /> {lab.estMinutes} MIN
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-success/30 px-2.5 py-1 font-mono text-[11px] uppercase text-success">
              <Icon name="shield" size={12} /> Safe Educational Simulation
            </span>
          </div>
        </div>
      </div>

      {solved ? (
        <div className="mx-auto max-w-[1500px] px-5 py-10 sm:px-8">
          <CompletionState lab={lab} />
        </div>
      ) : (
        <div className="mx-auto grid max-w-[1500px] gap-5 px-4 py-5 sm:gap-6 sm:px-8 sm:py-6 md:grid-cols-[1fr_330px] lg:grid-cols-[270px_1fr_330px]">
          {/* LEFT — mission */}
          <aside className="space-y-4">
            <div className="rounded-2xl border border-border bg-card p-5">
              <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
                <Icon name="compass" size={14} /> Mission
              </div>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{lab.mission}</p>
            </div>

            <div className="rounded-2xl border border-border bg-card p-5">
              <div className="mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
                <Icon name="target" size={14} /> Objectives
              </div>
              <ul className="space-y-2.5">
                {lab.objectives.map((o, i) => (
                  <li key={o} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                    <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border border-border font-mono text-[10px] text-subtle">
                      {i + 1}
                    </span>
                    {o}
                  </li>
                ))}
              </ul>
            </div>

            {lab.security && (
              <div className="rounded-2xl border border-border bg-card p-5">
                <div className="mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
                  <Icon name="shield" size={14} /> Threat model
                </div>
                <dl className="space-y-3">
                  {[
                    { label: "Asset", value: lab.security.asset },
                    { label: "Threat", value: lab.security.threat },
                    { label: "Weakness", value: lab.security.weakness },
                  ].map((row) => (
                    <div key={row.label}>
                      <dt className="font-mono text-[10px] uppercase tracking-widest text-subtle">
                        {row.label}
                      </dt>
                      <dd className="mt-0.5 text-sm leading-relaxed text-muted-foreground">
                        {row.value}
                      </dd>
                    </div>
                  ))}
                </dl>
                <div className="mt-3 flex items-start gap-2 rounded-lg bg-success/5 p-3 text-xs leading-relaxed text-success">
                  <Icon name="lock" size={13} className="mt-0.5 shrink-0" />
                  <span>{lab.security.safeBoundary}</span>
                </div>
              </div>
            )}

            <div className="rounded-2xl border border-border bg-card p-5">
              <div className="mb-2 flex items-center justify-between font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                <span>Progress</span>
                <span>{pct}%</span>
              </div>
              <ProgressBar value={pct} accent={lab.accent} />
              <div className="mt-3 flex justify-between font-mono text-[11px] text-subtle">
                <span>{doneCount}/{stages.length} steps</span>
                <span>{p.hintsUsed} hints</span>
              </div>
            </div>
          </aside>

          {/* CENTER — simulation + stepper */}
          <main className="space-y-6">
            <div>
              <div className="mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                <Icon name="cpu" size={14} className="text-cyan" /> Simulation
              </div>
              <Simulation lab={lab} onInteraction={handleInteraction} />
            </div>

            {/* stepper */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
                <Icon name="route" size={14} /> Investigation steps
              </div>
              {stages.map((stage, i) => {
                const stepState = sp[stage.id];
                const done = Boolean(stepState?.done);
                const active = i === activeIndex;
                return (
                  <div
                    key={stage.id}
                    className={cx(
                      "rounded-2xl border p-5 transition-colors",
                      done
                        ? "border-success/30 bg-success/[0.04]"
                        : active
                          ? wrongStep === stage.id
                            ? "border-danger/40 bg-card"
                            : "border-cyan/40 bg-card"
                          : "border-border bg-card/50 opacity-60",
                      active && shake && "animate-[pop-in_0.4s]",
                    )}
                    style={active && shake ? { animation: "pop-in 0.4s" } : undefined}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={cx(
                          "grid h-7 w-7 shrink-0 place-items-center rounded-full border font-mono text-[11px]",
                          done
                            ? "border-success/40 bg-success/15 text-success"
                            : active
                              ? "border-cyan/50 bg-cyan/10 text-cyan"
                              : "border-border text-subtle",
                        )}
                      >
                        {done ? <Icon name="check" size={14} strokeWidth={3} /> : i + 1}
                      </span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-semibold text-foreground">{stage.title}</h3>
                          <span className="font-mono text-[9px] uppercase tracking-widest text-subtle">
                            {stage.kind}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* completed step: show explanation */}
                    {done && stage.explanation && (
                      <p className="mt-3 pl-10 text-sm leading-relaxed text-muted-foreground">
                        {stage.explanation}
                      </p>
                    )}

                    {/* active step body */}
                    {active && !done && (
                      <div className="mt-3 pl-10">
                        <p className="text-sm leading-relaxed text-muted-foreground">{stage.prompt}</p>

                        {stage.kind === "decide" ? (
                          <div className="mt-4">
                            <p className="text-sm font-medium text-foreground">{stage.question}</p>
                            <div className="mt-3 space-y-2">
                              {stage.options?.map((o) => {
                                const sel = choiceByStep[stage.id] === o.id;
                                return (
                                  <label
                                    key={o.id}
                                    className={cx(
                                      "flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition-colors",
                                      sel
                                        ? "border-cyan/50 bg-cyan/5"
                                        : "border-border hover:bg-muted/30",
                                    )}
                                  >
                                    <input
                                      type="radio"
                                      name={`answer-${stage.id}`}
                                      value={o.id}
                                      checked={sel}
                                      onChange={() => {
                                        setChoiceByStep((c) => ({ ...c, [stage.id]: o.id }));
                                        setWrongStep(null);
                                      }}
                                      className="sr-only"
                                    />
                                    <span
                                      className={cx(
                                        "grid h-5 w-5 shrink-0 place-items-center rounded-full border",
                                        sel ? "border-cyan bg-cyan text-background" : "border-subtle",
                                      )}
                                    >
                                      {sel && <Icon name="check" size={12} strokeWidth={3} />}
                                    </span>
                                    <span className="text-sm text-foreground">{o.label}</span>
                                  </label>
                                );
                              })}
                            </div>

                            {wrongStep === stage.id && stage.wrongFeedback && (
                              <div className="mt-3 flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/5 p-3 text-sm text-danger">
                                <Icon name="x" size={16} className="mt-0.5 shrink-0" />
                                <span>{stage.wrongFeedback}</span>
                              </div>
                            )}

                            <PremiumButton
                              className="mt-4"
                              iconRight="arrow-right"
                              onClick={() => submitDecide(stage)}
                              disabled={!choiceByStep[stage.id]}
                            >
                              Submit answer
                            </PremiumButton>
                          </div>
                        ) : stage.requires && stage.requires.length > 0 ? (
                          <div className="mt-3 flex items-center gap-2 rounded-lg border border-dashed border-cyan/30 bg-cyan/5 px-3 py-2.5 font-mono text-[11px] text-cyan">
                            <Icon name="cpu" size={13} />
                            Perform this in the simulation above to continue.
                          </div>
                        ) : (
                          <PremiumButton
                            className="mt-3"
                            variant="outline"
                            iconRight="arrow-right"
                            onClick={() => markStepDone(lab.id, stage.id)}
                          >
                            I've reviewed this — continue
                          </PremiumButton>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </main>

          {/* RIGHT — intelligence */}
          <aside className="space-y-4">
            <HintPanel lab={lab} />
            <EvidencePanel lab={lab} />
          </aside>
        </div>
      )}
    </div>
  );
}
