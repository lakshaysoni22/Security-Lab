# Labs

All lab content lives in `src/lib/labs.ts` as a typed `Lab[]` (`LABS`). The lab
workspace (`src/pages/LabWorkspace.tsx`) and the simulation renderer
(`src/components/lab/Simulation.tsx`) are generic — they read a lab's data and
render the matching UI, so adding a lab is a data change, not a component change.

## The `Lab` data model

Defined in `src/lib/types.ts`:

| Field | Purpose |
|-------|---------|
| `id` | Stable key used in routes (`{ name: "lab", labId }`) and storage. |
| `number` | Display order (1–5). |
| `title` / `codename` | Human title and short domain name. |
| `slug?` | URL-style id mirroring the `/labs/[slug]` model. |
| `prerequisiteLabs?` | Informational ordering (lab ids to do first). |
| `security?` | Threat model — see below and `docs/SECURITY.md`. |
| `category` / `difficulty` / `estMinutes` / `accent` | Metadata + theming. |
| `skills` | Chips shown on cards. |
| `summary` / `mission` / `objectives` | Briefing copy. |
| `simulation` | `"browser" \| "request" \| "config" \| "form"` — which renderer. |
| `sim` | Free-form payload consumed by the chosen renderer. |
| `hints` | Tiered hints (each revealed one costs score). |
| `steps?` | The multi-step investigation (see below). When present, the workspace runs the stepper and this drives completion. |
| `finalAssessment?` | An optional combined final question (used by Lab 05). |
| `question` / `options` / `answer` / `wrongFeedback` | Legacy single-challenge fallback for labs without `steps`. |
| `baseScore` | Legacy field; the standardized scorer uses a fixed base of 100. |
| `outcome` | Completion copy: discovered / whyItMatters / secureApproach / nextSkill. |

## Multi-step investigations

Each lab is a sequence of `LabStep`s (`src/lib/types.ts`) forming an
observe → probe → decide flow:

- **`observe` / `probe`** — the learner interacts with the simulation. The step
  auto-completes once every tag in `requires` has been reported by the sim (or via
  a "Continue" affordance when `requires` is empty).
- **`decide`** — an embedded multiple-choice sub-question, scored like the final
  challenge.

Per-step state (`done`, `attempts`, `choice`, `interactions`) is stored in
`LabProgress.stepProgress` and persisted. The workspace progress bar reflects real
completed-steps ÷ total-steps. A lab completes only when every step (and
`finalAssessment`, if present) is satisfied.

The current flows: **Lab 01** compare valid vs invalid login → name the enumeration
weakness → pick the control. **Lab 02** open your record → request another via its id
→ explain IDOR → choose the server-side fix. **Lab 03** run the 7-test input toolbox →
identify XSS → choose the control set. **Lab 04** review config by section → flag findings
by severity → rank the worst → compare the hardened baseline → name the principle.
**Lab 05** explore the request/response inspector → 5 focused sub-challenges → a combined
final assessment.

## Simulation kinds

- **browser** — a simulated browser (`BrowserFrame`) with an address bar and
  scripted responses/records (labs 01, 02).
- **form** — the input **test toolbox**: 7 predefined, deterministic test inputs
  rendered into a results table. The one "unexpected characters" test renders a
  fixed, predefined payload as HTML to demonstrate reflected XSS inside the
  isolated lab only. No user-typed input is ever executed as code (lab 03).
- **config** — a static, fictional config manifest grouped by section with
  per-line severity, a flagging interaction, and a hardened before/after
  baseline (lab 04).
- **request** — a captured request/response pair via `RequestViewer`, with tabs,
  copy, and a safer-response comparison (lab 05).

All payloads are static and in-memory. No renderer performs network I/O. Each sim
receives an `onInteraction(tag)` callback and reports interaction tags; the
workspace routes those tags to the step that `requires` them.

## Scoring (standardized)

Every lab uses a fixed base of **100**, minus **3 per wrong sub-answer attempt**
(summed across all steps) and **5 per hint revealed**, with a **floor of 60**
(`computeScore` in `src/lib/labs.ts`). Replaying a completed lab hint-free is the
intended way to raise a score; `RecommendationEngine` surfaces the lowest-scoring
completed lab for replay.

> Progress saved before this model is preserved as-is (old scores kept). Only
> replays and newly completed labs use the standardized score.

## Adding a lab (e.g. "Lab 6")

1. Append a `Lab` object to `LABS` (`src/lib/labs.ts`) with a unique `id`, the next
   `number`, a `simulation` kind, and a `sim` payload the matching renderer
   understands.
2. Author its `steps` array (observe/probe/decide). For observe/probe steps, set
   `requires` to the interaction tags your sim reports; for decide steps, provide
   `question`/`options`/`answer`/`wrongFeedback`/`explanation`. Add a
   `finalAssessment` only if you want a combined closing question.
3. Add tiered `hints`, `outcome` copy, and a `security` block (all fields) so it
   appears on the Safety page and the workspace threat-model panel.
4. Add its category to `SKILL_AXES` if it introduces a new skill domain.
5. No engine or component edits are required — the stepper, scoring, hints,
   evidence, progress and achievements all read the data model. (If your lab needs
   a brand-new interaction style, add a renderer branch in `Simulation.tsx`.)
