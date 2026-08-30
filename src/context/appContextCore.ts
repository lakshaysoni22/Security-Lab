import { createContext, useContext, useEffect, useState } from "react";
import type { EvidenceItem, LabProgress, PersistState, Route } from "../lib/types";

export interface AppValue {
  route: Route;
  navigate: (route: Route) => void;
  state: PersistState;
  labProgress: (id: string) => LabProgress;
  totalScore: number;
  completedCount: number;
  startLab: (id: string) => void;
  useHint: (id: string) => void;
  addEvidence: (id: string, observation: string, category: string) => void;
  removeEvidence: (id: string, evidenceId: string) => void;
  submitAnswer: (id: string, choice: string) => boolean;
  /** Record an interaction tag against an observe/probe step (auto-completes it). */
  addInteraction: (id: string, stepId: string, tag: string) => void;
  /** Mark an observe/probe step done (Continue affordance for steps with no requires). */
  markStepDone: (id: string, stepId: string) => void;
  /** Answer a decide-step or the final assessment; returns whether it was correct. */
  submitStep: (id: string, stepId: string, choice: string) => boolean;
  addTime: (id: string, ms: number) => void;
  reset: () => void;
  newlyUnlocked: string[];
  clearUnlocked: () => void;
}

// Kept in its own module (no component exports) so the context object keeps a
// stable identity across Fast Refresh / HMR updates.
export const AppCtx = createContext<AppValue | null>(null);

export function useApp(): AppValue {
  const v = useContext(AppCtx);
  if (!v) throw new Error("useApp must be used within AppProvider");
  return v;
}

/** Reduced-motion hook shared across animated components. */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}

export type { EvidenceItem };
