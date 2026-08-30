import type { PersistState } from "./types";
import { LABS } from "./labs";

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: "flag" | "shield" | "zap" | "target" | "crown" | "eye";
  test: (s: PersistState) => boolean;
}

export const ACHIEVEMENTS: Achievement[] = [
  {
    id: "first-blood",
    title: "First Contact",
    description: "Complete your first investigation.",
    icon: "flag",
    test: (s) => Object.values(s.labs).some((l) => l.status === "completed"),
  },
  {
    id: "no-hints",
    title: "Lone Analyst",
    description: "Complete a lab without using a single hint.",
    icon: "eye",
    test: (s) =>
      Object.values(s.labs).some((l) => l.status === "completed" && l.hintsUsed === 0),
  },
  {
    id: "first-try",
    title: "Sharp Instinct",
    description: "Solve a lab correctly on the first attempt.",
    icon: "target",
    test: (s) =>
      Object.values(s.labs).some((l) => l.status === "completed" && l.attempts <= 1),
  },
  {
    id: "halfway",
    title: "Field Operative",
    description: "Complete three investigations.",
    icon: "zap",
    test: (s) => Object.values(s.labs).filter((l) => l.status === "completed").length >= 3,
  },
  {
    id: "all-clear",
    title: "Threat Hunter",
    description: "Complete all five labs.",
    icon: "shield",
    test: (s) =>
      Object.values(s.labs).filter((l) => l.status === "completed").length === LABS.length,
  },
  {
    id: "high-score",
    title: "Command Grade",
    description: "Average 90+ across the five labs (total score 450 or more).",
    icon: "crown",
    test: (s) => Object.values(s.labs).reduce((a, l) => a + l.score, 0) >= 450,
  },
];

export function evaluateAchievements(state: PersistState): string[] {
  const unlocked = new Set(state.achievements);
  for (const a of ACHIEVEMENTS) {
    if (a.test(state)) unlocked.add(a.id);
  }
  return [...unlocked];
}
