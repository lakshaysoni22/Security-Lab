# Architecture

## Overview

TrinetLayer is a single-page React app. There is **no router library** — routing
is state-based through a small context, which keeps the whole app in one tree and
makes every view trivially shareable and persistable.

```
index.html → src/main.tsx → src/App.tsx
                               └─ AppProvider (context)
                                  └─ Shell
                                     ├─ AuroraBackground / ScrollProgress (fx)
                                     ├─ Navbar
                                     ├─ CurrentView  ← switch on route.name
                                     ├─ Footer
                                     └─ AchievementToast
```

## Routing

`Route` is a discriminated union in `src/lib/types.ts`:

```
home | labs | dashboard | learning | resources
progress | achievements | about | safety | notfound
lab (labId)
```

`CurrentView` in `src/App.tsx` switches on `route.name`. The `default` branch
renders `<NotFound />`, so any unknown route behaves like a real 404. Navigation
is `navigate(route)` from `useApp()`.

## State & persistence

- **`src/context/appContextCore.ts`** — the context object, `useApp()`, and
  `usePrefersReducedMotion()`. This module intentionally exports **no React
  components**, so the context keeps a stable identity across Fast Refresh / HMR.
- **`src/context/AppContext.tsx`** — the `AppProvider` component; hydrates from
  storage, exposes actions (`navigate`, `startLab`, `useHint`, `addEvidence`,
  `submitAnswer`, `addTime`, `reset`) plus the multi-step actions
  (`addInteraction`, `markStepDone`, `submitStep`), and persists on change.
- **`src/lib/storage.ts`** — typed `localStorage` load/save under the versioned
  key `trinetlayer.v1`. `loadState` backfills the additive `stepProgress` map for
  saves written before the multi-step model.
- **`src/lib/types.ts`** — `Lab`, `LabStep`, `FinalAssessment`, `LabProgress`,
  `LabStepProgress`, `PersistState`, `Route`, `LabSecurity`, etc.

## Multi-step investigations

Each lab is an ordered list of `LabStep`s (`observe` / `probe` / `decide`) plus an
optional `finalAssessment`. Rather than a single `submitAnswer`, the workspace
drives a stepper:

- **Sim → context channel.** `src/components/lab/Simulation.tsx` (and
  `RequestViewer`) receive an `onInteraction(tag)` callback. Each observe/probe
  step declares the interaction tags it `requires`; when a sim reports every
  required tag, `addInteraction` auto-marks the step done. `markStepDone` covers
  steps with no required interaction (a "continue" affordance).
- **Deciding.** `submitStep(labId, stepId, choice)` scores a `decide` step (or the
  final assessment): it increments that step's attempt count on a wrong choice and
  records the choice on a correct one, returning correctness.
- **Completion.** A lab finishes only when every step (and `finalAssessment`, if
  present) is satisfied; the provider then finalizes the standardized score,
  unlocks the next lab, and re-evaluates achievements. Labs without `steps` keep
  the legacy single-MCQ `submitAnswer` path.

## Scoring

`computeScore(wrongAttempts, hintsUsed)` in `src/lib/labs.ts` is the single source
of truth: **base 100 − 3 per wrong sub-answer attempt − 5 per hint, floored at
60** (`SCORE_BASE` / `SCORE_PER_WRONG` / `SCORE_PER_HINT` / `SCORE_FLOOR`). Wrong
attempts are summed across every step in the lab. Progress saved before this model
keeps its old score; only replays and new completions use it.

## The learning engine

`src/lib/engine.ts` is a **pure, deterministic, offline** layer over saved
state:

- `RecommendationEngine.nextLab(state)` — resume in-progress → first available →
  replay lowest-scoring completed.
- `LearningEngine.skillProfile(state)` (rescaled for the base-100 model) /
  `weakestSkill(state)` / `summary(state)`, plus `strengths(state)`,
  `weaknesses(state)`, and `recommendedConcept(state)` surfaced on `/progress`.
- `HintEngine.revealedHints` / `nextHint` / `remaining`, and the adaptive
  `suggestHint(lab, progress)` — a deterministic read of learner signals
  (attempts, time, hints used) that decides when to nudge the learner toward a
  hint. Fully offline; consumed by `HintPanel`.
- `AdaptiveLearningProvider` interface + `LocalHeuristicProvider` (the default). A custom
  provider can implement `AdaptiveLearningProvider` and be swapped in via
  `activeProvider` with **no UI changes**. The app is fully functional with the
  default provider and zero external dependencies.

The dashboard and progress pages consume the engine rather than duplicating
selection logic.

## UI system

- **`src/components/ui/primitives.tsx`** — `PremiumButton`, `GlowCard`,
  `GlassPanel`, `SectionHeader`, `StatusBadge`, `DifficultyBadge`, `Chip`,
  `ProgressRing`, `ProgressBar`, `MetricCard`, `Reveal`, `CountUp`, `Tilt`, and
  the shared `useInView` hook. Colour helpers: `accentText`, `accentHex`, `cx`.
- **`src/components/ui/Icon.tsx`** — a single inline-SVG icon set (`IconName`).
- **`src/components/fx/`** — `AuroraBackground`, `Confetti`, `DrawCheck`,
  `ScrollProgress` (all Canvas/CSS, reduced-motion-safe).
- **`src/components/lab/`** — the lab workspace pieces: `Simulation`,
  `BrowserFrame`, `RequestViewer`, `HintPanel`, `EvidencePanel`,
  `CompletionState`.
- **`src/pages/`** — one file per view.

## Styling

Tailwind CSS v4 is imported in `src/index.css`, which also defines the `@theme`
design tokens, fonts (`@import` first), keyframes, and the
`prefers-reduced-motion` guard. There is **no** unlayered `*` reset.

## Conventions

- Components use **named exports** (matches the existing scaffold), except
  `App.tsx` which is the default entry component.
- All new type fields are **additive/optional** so existing persisted state and
  labs remain valid.
- Every animation has a reduced-motion path; nothing may cause horizontal
  overflow.
