import type { Lab, LabProgress, PersistState } from "./types";
import { LABS, SKILL_AXES, getLab } from "./labs";

/**
 * TrinetLayer learning engine.
 *
 * A pure, deterministic, fully-offline analytics engine that turns saved progress into
 * recommendations, skill profiles, and adaptive hint ordering. It operates completely
 * client-side with zero external API latency or privacy risk.
 */

/* ------------------------------------------------------------------ helpers */

function progressOf(state: PersistState, id: string): LabProgress | undefined {
  return state.labs[id];
}

function completedCount(state: PersistState): number {
  return Object.values(state.labs).filter((l) => l.status === "completed").length;
}

/* -------------------------------------------------------- RecommendationEngine */

export const RecommendationEngine = {
  /**
   * The single lab the learner should do next:
   *   1. resume anything in progress, else
   *   2. the first available (unlocked, not started) lab in path order, else
   *   3. replay the lowest-scoring completed lab to push mastery.
   * Returns undefined only when there are no labs at all.
   */
  nextLab(state: PersistState): Lab | undefined {
    const inProgress = LABS.find((l) => progressOf(state, l.id)?.status === "in-progress");
    if (inProgress) return inProgress;

    const available = LABS.find((l) => progressOf(state, l.id)?.status === "available");
    if (available) return available;

    const completed = LABS.filter((l) => progressOf(state, l.id)?.status === "completed");
    if (completed.length > 0) {
      return [...completed].sort(
        (a, b) => (progressOf(state, a.id)?.score ?? 0) - (progressOf(state, b.id)?.score ?? 0),
      )[0];
    }
    return LABS[0];
  },

  /** Short reason string for why a lab is recommended (for UI copy). */
  reasonFor(state: PersistState, lab: Lab): string {
    const status = progressOf(state, lab.id)?.status;
    if (status === "in-progress") return "Resume your active investigation";
    if (status === "completed") return "Replay hint-free to raise your score";
    if (completedCount(state) === 0) return "Start here — the recommended first case";
    return "The next case on your learning path";
  },
};

/* ------------------------------------------------------------- LearningEngine */

export interface SkillAxisScore {
  key: string;
  labId: string;
  /** Normalised mastery 0..1. */
  value: number;
}

export const LearningEngine = {
  /** Per-axis normalised mastery, mirroring the SkillRadar model. */
  skillProfile(state: PersistState): SkillAxisScore[] {
    return SKILL_AXES.map((axis) => {
      const labId = axis.labs[0];
      const p = progressOf(state, labId);
      let value = 0;
      if (p) {
        // Base-100 model: a completed lab maps score 60→0.8, 100→1.0.
        if (p.status === "completed") value = Math.min(1, 0.5 + (p.score / 100) * 0.5);
        else if (p.status === "in-progress") value = 0.35;
        else if (p.status === "available") value = 0.12;
        else value = 0.06;
      }
      return { key: axis.key, labId, value };
    });
  },

  /** The weakest skill axis — useful for "focus next on…" copy. */
  weakestSkill(state: PersistState): SkillAxisScore | undefined {
    const profile = this.skillProfile(state);
    if (profile.length === 0) return undefined;
    return [...profile].sort((a, b) => a.value - b.value)[0];
  },

  /** Completed axes at strong mastery (factual, not psychological). */
  strengths(state: PersistState): SkillAxisScore[] {
    return this.skillProfile(state)
      .filter((a) => a.value >= 0.9)
      .sort((a, b) => b.value - a.value);
  },

  /** Axes not yet demonstrated or completed below full marks. */
  weaknesses(state: PersistState): SkillAxisScore[] {
    return this.skillProfile(state)
      .filter((a) => a.value < 0.8)
      .sort((a, b) => a.value - b.value);
  },

  /** The concept to focus on next: the weakest axis with a labId to jump to. */
  recommendedConcept(state: PersistState): SkillAxisScore | undefined {
    return this.weaknesses(state)[0] ?? this.weakestSkill(state);
  },

  /** One-line human summary of overall standing. */
  summary(state: PersistState): string {
    const done = completedCount(state);
    if (done === 0) return "No investigations closed yet — your skill matrix is waiting.";
    if (done === LABS.length) return "Every domain covered. Replay labs to deepen mastery.";
    const weakest = this.weakestSkill(state);
    return weakest
      ? `${done} of ${LABS.length} closed. Your thinnest area is ${weakest.key}.`
      : `${done} of ${LABS.length} investigations closed.`;
  },
};

/* ---------------------------------------------------------------- HintEngine */

export const HintEngine = {
  /**
   * Hints the learner has already unlocked, in order. Purely presentational —
   * scoring/penalty semantics stay in AppContext.
   */
  revealedHints(lab: Lab, hintsUsed: number): string[] {
    return lab.hints.slice(0, Math.min(hintsUsed, lab.hints.length));
  },

  /** The next hint to reveal, or undefined when all are exhausted. */
  nextHint(lab: Lab, hintsUsed: number): string | undefined {
    return lab.hints[hintsUsed];
  },

  remaining(lab: Lab, hintsUsed: number): number {
    return Math.max(0, lab.hints.length - hintsUsed);
  },

  /**
   * Adaptive, deterministic suggestion of *when* to surface a hint, from signals
   * already in saved state — no psychological claims, no network. The learner
   * always stays in control; this only nudges.
   */
  suggestHint(
    lab: Lab,
    progress: LabProgress,
  ): { offer: boolean; reason: string } {
    if (this.remaining(lab, progress.hintsUsed) === 0) {
      return { offer: false, reason: "All hints revealed — trust your investigation." };
    }
    const sp = progress.stepProgress ?? {};
    const wrong = Object.values(sp).reduce((a, s) => a + (s.attempts ?? 0), 0);
    const stuckMinutes = Math.round(progress.timeSpentMs / 60000);
    if (wrong >= 2) {
      return { offer: true, reason: "A couple of answers missed — a hint can refocus you." };
    }
    if (stuckMinutes >= Math.max(6, lab.estMinutes) && progress.hintsUsed === 0) {
      return { offer: true, reason: "You've been at this a while — a nudge is available." };
    }
    if (progress.hintsUsed === 0) {
      return { offer: false, reason: "Try the simulation first — hints cost points." };
    }
    return { offer: false, reason: "You're making progress — keep going." };
  },
};

/* ---------------------------------------------------- AdaptiveLearningProvider */

/**
 * Adaptive learning provider abstraction. The default implementation is the local
 * deterministic heuristic engine above (no external dependencies, 100% offline).
 */
export interface AdaptiveLearningProvider {
  readonly id: string;
  recommendNextLab(state: PersistState): Lab | undefined;
  explainRecommendation(state: PersistState, lab: Lab): string;
  summariseProgress(state: PersistState): string;
}

export const LocalHeuristicProvider: AdaptiveLearningProvider = {
  id: "local-heuristic",
  recommendNextLab: (state) => RecommendationEngine.nextLab(state),
  explainRecommendation: (state, lab) => RecommendationEngine.reasonFor(state, lab),
  summariseProgress: (state) => LearningEngine.summary(state),
};

export const activeProvider: AdaptiveLearningProvider = LocalHeuristicProvider;

export { getLab };
