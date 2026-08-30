import type { LabProgress, PersistState } from "./types";
import { LABS } from "./labs";

const KEY = "cyber-labs.v1";
const VERSION = 1;

export function emptyLabProgress(): LabProgress {
  return {
    status: "available",
    score: 0,
    attempts: 0,
    hintsUsed: 0,
    timeSpentMs: 0,
    evidence: [],
    stepProgress: {},
  };
}

export function defaultState(): PersistState {
  const labs: Record<string, LabProgress> = {};
  LABS.forEach((lab, i) => {
    labs[lab.id] = {
      ...emptyLabProgress(),
      // First lab open; the rest locked until the previous completes.
      status: i === 0 ? "available" : "locked",
    };
  });
  return { version: VERSION, labs, achievements: [], learnerName: "Analyst" };
}

export function loadState(): PersistState {
  if (typeof window === "undefined") return defaultState();
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw) as PersistState;
    if (parsed.version !== VERSION) return defaultState();
    // Backfill any labs added since the save.
    const base = defaultState();
    parsed.labs = { ...base.labs, ...parsed.labs };
    // Backfill stepProgress for saves created before multi-step labs existed.
    for (const id of Object.keys(parsed.labs)) {
      if (!parsed.labs[id].stepProgress) parsed.labs[id].stepProgress = {};
    }
    return parsed;
  } catch {
    return defaultState();
  }
}

export function saveState(state: PersistState): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* storage full or blocked — non-fatal */
  }
}

export function resetState(): PersistState {
  const fresh = defaultState();
  saveState(fresh);
  return fresh;
}
