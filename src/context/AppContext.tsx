import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";
import type { EvidenceItem, Lab, LabProgress, LabStepProgress, PersistState, Route } from "../lib/types";
import { FINAL_STEP_ID, LABS, computeScore, getLab } from "../lib/labs";
import { defaultState, loadState, resetState, saveState } from "../lib/storage";
import { evaluateAchievements } from "../lib/achievements";
import { AppCtx } from "./appContextCore";
import type { AppValue } from "./appContextCore";

export { useApp, usePrefersReducedMotion } from "./appContextCore";

/* ---------------------------------------------------------------- step helpers */

function emptyStep(): LabStepProgress {
  return { done: false, attempts: 0, interactions: [] };
}

/** True when every step (and the final assessment, if any) is satisfied. */
function allStepsDone(lab: Lab, sp: Record<string, LabStepProgress>): boolean {
  const steps = lab.steps ?? [];
  if (steps.length === 0) return false;
  const stepsOk = steps.every((s) => sp[s.id]?.done);
  const finalOk = !lab.finalAssessment || sp[FINAL_STEP_ID]?.done;
  return stepsOk && Boolean(finalOk);
}

/** Total wrong attempts across all recorded steps — feeds the standardized score. */
function totalWrongAttempts(sp: Record<string, LabStepProgress>): number {
  return Object.values(sp).reduce((a, s) => a + (s.attempts ?? 0), 0);
}

/**
 * If the lab's steps are all satisfied, finalize it: standardized score,
 * completed status, unlock the next lab. Returns the (possibly) updated labs map.
 */
function finalizeIfComplete(
  lab: Lab,
  labs: Record<string, LabProgress>,
  id: string,
): Record<string, LabProgress> {
  const p = labs[id];
  if (!p || p.status === "completed") return labs;
  const sp = p.stepProgress ?? {};
  if (!allStepsDone(lab, sp)) return labs;

  const score = computeScore(totalWrongAttempts(sp), p.hintsUsed);
  const next = LABS[LABS.findIndex((l) => l.id === id) + 1];
  const updated: Record<string, LabProgress> = {
    ...labs,
    [id]: { ...p, status: "completed", score, completedAt: Date.now() },
  };
  if (next && updated[next.id]?.status === "locked") {
    updated[next.id] = { ...updated[next.id], status: "available" };
  }
  return updated;
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [route, setRoute] = useState<Route>({ name: "home" });
  const [state, setState] = useState<PersistState>(() =>
    typeof window === "undefined" ? defaultState() : loadState(),
  );
  const [newlyUnlocked, setNewlyUnlocked] = useState<string[]>([]);

  // Persist on every change.
  useEffect(() => {
    saveState(state);
  }, [state]);

  // Detect newly unlocked achievements by diffing against what we last saw.
  const seenAchievements = useRef<string[]>(state.achievements);
  useEffect(() => {
    const prev = new Set(seenAchievements.current);
    const fresh = state.achievements.filter((a) => !prev.has(a));
    if (fresh.length) setNewlyUnlocked((cur) => [...cur, ...fresh]);
    seenAchievements.current = state.achievements;
  }, [state.achievements]);

  const navigate = useCallback((r: Route) => {
    setRoute(r);
    if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "auto" });
  }, []);

  const labProgress = useCallback(
    (id: string) => state.labs[id] ?? defaultState().labs[id],
    [state.labs],
  );

  const startLab = useCallback((id: string) => {
    setState((s) => {
      const lab = s.labs[id];
      if (!lab || lab.status === "locked") return s;
      if (lab.status === "completed") return s;
      return {
        ...s,
        labs: {
          ...s.labs,
          [id]: {
            ...lab,
            status: "in-progress",
            startedAt: lab.startedAt ?? Date.now(),
          },
        },
      };
    });
  }, []);

  const useHint = useCallback((id: string) => {
    setState((s) => {
      const lab = s.labs[id];
      if (!lab) return s;
      return { ...s, labs: { ...s.labs, [id]: { ...lab, hintsUsed: lab.hintsUsed + 1 } } };
    });
  }, []);

  const addEvidence = useCallback((id: string, observation: string, category: string) => {
    setState((s) => {
      const lab = s.labs[id];
      if (!lab) return s;
      const item: EvidenceItem = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        index: lab.evidence.length + 1,
        observation,
        category,
        createdAt: Date.now(),
      };
      return { ...s, labs: { ...s.labs, [id]: { ...lab, evidence: [...lab.evidence, item] } } };
    });
  }, []);

  const removeEvidence = useCallback((id: string, evidenceId: string) => {
    setState((s) => {
      const lab = s.labs[id];
      if (!lab) return s;
      const evidence = lab.evidence
        .filter((e) => e.id !== evidenceId)
        .map((e, i) => ({ ...e, index: i + 1 }));
      return { ...s, labs: { ...s.labs, [id]: { ...lab, evidence } } };
    });
  }, []);

  const addInteraction = useCallback((id: string, stepId: string, tag: string) => {
    const lab = getLab(id);
    if (!lab) return;
    const step = lab.steps?.find((s) => s.id === stepId);
    if (!step) return;
    setState((s) => {
      const p = s.labs[id];
      if (!p) return s;
      const sp = { ...(p.stepProgress ?? {}) };
      const cur = sp[stepId] ?? emptyStep();
      if (cur.done) return s;
      const interactions = cur.interactions?.includes(tag)
        ? cur.interactions
        : [...(cur.interactions ?? []), tag];
      const required = step.requires ?? [];
      const done = required.length > 0 && required.every((r) => interactions.includes(r));
      sp[stepId] = { ...cur, interactions, done };
      return { ...s, labs: { ...s.labs, [id]: { ...p, stepProgress: sp } } };
    });
  }, []);

  const markStepDone = useCallback((id: string, stepId: string) => {
    setState((s) => {
      const p = s.labs[id];
      if (!p) return s;
      const sp = { ...(p.stepProgress ?? {}) };
      const cur = sp[stepId] ?? emptyStep();
      if (cur.done) return s;
      sp[stepId] = { ...cur, done: true };
      return { ...s, labs: { ...s.labs, [id]: { ...p, stepProgress: sp } } };
    });
  }, []);

  const submitStep = useCallback((id: string, stepId: string, choice: string): boolean => {
    const lab = getLab(id);
    if (!lab) return false;
    const answer =
      stepId === FINAL_STEP_ID
        ? lab.finalAssessment?.answer
        : lab.steps?.find((s) => s.id === stepId)?.answer;
    if (answer === undefined) return false;
    const correct = choice === answer;
    setState((s) => {
      const p = s.labs[id];
      if (!p) return s;
      const sp = { ...(p.stepProgress ?? {}) };
      const cur = sp[stepId] ?? emptyStep();
      if (cur.done) return s;
      if (!correct) {
        sp[stepId] = { ...cur, attempts: cur.attempts + 1 };
        return { ...s, labs: { ...s.labs, [id]: { ...p, stepProgress: sp } } };
      }
      sp[stepId] = { ...cur, done: true, choice };
      const labsWithStep = { ...s.labs, [id]: { ...p, stepProgress: sp } };
      const labs = finalizeIfComplete(lab, labsWithStep, id);
      const withLabs = { ...s, labs };
      return { ...withLabs, achievements: evaluateAchievements(withLabs) };
    });
    return correct;
  }, []);

  const addTime = useCallback((id: string, ms: number) => {
    if (ms <= 0) return;
    setState((s) => {
      const lab = s.labs[id];
      if (!lab) return s;
      return { ...s, labs: { ...s.labs, [id]: { ...lab, timeSpentMs: lab.timeSpentMs + ms } } };
    });
  }, []);

  const submitAnswer = useCallback((id: string, choice: string): boolean => {
    const lab = getLab(id);
    if (!lab) return false;
    const correct = choice === lab.answer;
    setState((s) => {
      const p = s.labs[id];
      if (!p) return s;
      const attempts = p.attempts + 1;
      if (!correct) {
        return { ...s, labs: { ...s.labs, [id]: { ...p, attempts } } };
      }
      // Standardized score: base 100 − 3/wrong attempt − 5/hint, floor 60.
      const score = computeScore(Math.max(0, attempts - 1), p.hintsUsed);
      const idx = LABS.findIndex((l) => l.id === id);
      const nextLab = LABS[idx + 1];
      const labs = {
        ...s.labs,
        [id]: {
          ...p,
          attempts,
          status: "completed" as const,
          score,
          completedAt: Date.now(),
        },
      };
      if (nextLab && labs[nextLab.id]?.status === "locked") {
        labs[nextLab.id] = { ...labs[nextLab.id], status: "available" };
      }
      const withLabs = { ...s, labs };
      return { ...withLabs, achievements: evaluateAchievements(withLabs) };
    });
    return correct;
  }, []);

  const reset = useCallback(() => {
    setState(resetState());
    setNewlyUnlocked([]);
  }, []);

  const clearUnlocked = useCallback(() => setNewlyUnlocked([]), []);

  const totalScore = useMemo(
    () => Object.values(state.labs).reduce((a, l) => a + l.score, 0),
    [state.labs],
  );
  const completedCount = useMemo(
    () => Object.values(state.labs).filter((l) => l.status === "completed").length,
    [state.labs],
  );

  const value: AppValue = {
    route,
    navigate,
    state,
    labProgress,
    totalScore,
    completedCount,
    startLab,
    useHint,
    addEvidence,
    removeEvidence,
    submitAnswer,
    addInteraction,
    markStepDone,
    submitStep,
    addTime,
    reset,
    newlyUnlocked,
    clearUnlocked,
  };

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}
