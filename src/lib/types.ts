export type Route =
  | { name: "home" }
  | { name: "labs" }
  | { name: "dashboard" }
  | { name: "learning" }
  | { name: "resources" }
  | { name: "progress" }
  | { name: "achievements" }
  | { name: "about" }
  | { name: "safety" }
  | { name: "privacy" }
  | { name: "notfound" }
  | { name: "lab"; labId: string };

export type Difficulty = "Beginner" | "Intermediate" | "Advanced";

export type LabStatus = "locked" | "available" | "in-progress" | "completed";

export type SimulationKind = "browser" | "request" | "config" | "form";

export interface ChallengeOption {
  id: string;
  label: string;
  detail?: string;
}

/**
 * A single stage in a multi-step investigation.
 * - `observe` / `probe`: interact with the simulation. The step auto-completes
 *   once every tag in `requires` has been reported by the sim (or immediately,
 *   via a "Continue" affordance, when `requires` is empty).
 * - `decide`: an embedded multiple-choice sub-question, scored like the final
 *   challenge (−3 per wrong attempt).
 */
export type LabStepKind = "observe" | "probe" | "decide";

export interface LabStep {
  id: string;
  kind: LabStepKind;
  title: string;
  prompt: string;
  /** Interaction tags the sim must report before an observe/probe step is done. */
  requires?: string[];
  /** decide-step sub-question. */
  question?: string;
  options?: ChallengeOption[];
  answer?: string;
  wrongFeedback?: string;
  /** Shown after the step is completed correctly. */
  explanation?: string;
}

/** Lab 05's combined final assessment, drawing on every prior domain. */
export interface FinalAssessment {
  question: string;
  options: ChallengeOption[];
  answer: string;
  wrongFeedback: string;
  explanation?: string;
}

export interface LabStepProgress {
  done: boolean;
  /** Recorded choice for a decide-step once answered correctly. */
  choice?: string;
  /** Wrong attempts against this step (feeds standardized scoring). */
  attempts: number;
  /** Interaction tags reported by the sim for observe/probe steps. */
  interactions?: string[];
}

/**
 * Threat-model metadata for a lab. Optional so existing labs and any persisted
 * state remain valid; surfaced on the Safety page and in the lab workspace.
 */
export interface LabSecurity {
  /** What is being protected in the scenario. */
  asset: string;
  /** The adversary action the lab teaches you to recognise. */
  threat: string;
  /** The specific weakness that enables the threat. */
  weakness: string;
  /** What the learner should walk away understanding. */
  learningGoal: string;
  /** The hard boundary that keeps the simulation safe (no real targets). */
  safeBoundary: string;
  /** How the lab is considered solved. */
  successCondition: string;
  /** The defender's fix. */
  remediation: string;
}

export interface Lab {
  id: string;
  number: number;
  title: string;
  codename: string;
  /** URL-style identifier mirroring the master-build route model (`/labs/[slug]`). */
  slug?: string;
  /** Lab ids that should be completed first (informational ordering). */
  prerequisiteLabs?: string[];
  /** Structured threat model for the Safety page + lab workspace. */
  security?: LabSecurity;
  category: string;
  difficulty: Difficulty;
  estMinutes: number;
  accent: "cyan" | "primary" | "violet" | "warning" | "success";
  skills: string[];
  summary: string;
  mission: string;
  objectives: string[];
  simulation: SimulationKind;
  /** Free-form structured payload consumed by the simulation renderer. */
  sim: Record<string, unknown>;
  hints: string[];
  /**
   * Multi-step investigation. When present, the workspace runs the stepper and
   * the lab completes only when every step (and `finalAssessment`, if any) is
   * satisfied. Labs without `steps` fall back to the single-question path below.
   */
  steps?: LabStep[];
  finalAssessment?: FinalAssessment;
  question: string;
  options: ChallengeOption[];
  answer: string;
  wrongFeedback: string;
  baseScore: number;
  outcome: {
    discovered: string;
    whyItMatters: string;
    secureApproach: string;
    nextSkill: string;
  };
}

export interface EvidenceItem {
  id: string;
  index: number;
  observation: string;
  category: string;
  createdAt: number;
}

export interface LabProgress {
  status: LabStatus;
  score: number;
  attempts: number;
  hintsUsed: number;
  timeSpentMs: number;
  startedAt?: number;
  completedAt?: number;
  evidence: EvidenceItem[];
  /** Per-step state for multi-step labs; backfilled by loadState for old saves. */
  stepProgress?: Record<string, LabStepProgress>;
}

export interface PersistState {
  version: number;
  labs: Record<string, LabProgress>;
  achievements: string[];
  learnerName: string;
}
