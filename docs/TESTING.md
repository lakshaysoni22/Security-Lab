# Testing — Manual QA Checklist

This project runs in an environment where automated test runners and `build`
are unavailable, so quality is verified manually in the live preview. Work
through this checklist after any change; it exercises every route and the full
lab loop.

## Smoke

- [ ] App loads with no console errors or warnings.
- [ ] Tab title and shield favicon render.

## Navigation

- [ ] Navbar primary links (Labs, Learning, Dashboard) navigate correctly.
- [ ] Active link shows its underline/highlight state.
- [ ] Footer links reach Progress, Achievements, Resources, Safety, About, Overview.
- [ ] Mobile menu (narrow viewport) lists all destinations and closes on select.
- [ ] Navbar becomes solid/blurred on scroll; transparent on the hero at top.

## Landing page

- [ ] Hero renders (Canvas network) and degrades to the static skeleton/fallback.
- [ ] Scroll reveals fire once; stat numbers count up; learning-path spine draws.
- [ ] FAQ: each item expands/collapses via **click** and via **keyboard**
      (Tab to the button, Enter/Space); focus ring visible; `aria-expanded`
      toggles.

## Labs — the stepper (repeat for all five)

- [ ] Open the lab from Labs / Learning / Dashboard / Safety.
- [ ] Top bar shows lab number, difficulty, time, and "Safe Educational
      Simulation" badge.
- [ ] Threat-model panel shows asset / threat / weakness + safe boundary.
- [ ] Steps render as a stepper: exactly one active, earlier ones collapsed with a
      check, later ones pending.
- [ ] **observe/probe** steps auto-advance once the required simulation
      interaction is performed (or via "I've reviewed — continue" when none is
      required).
- [ ] **decide** steps: a wrong sub-answer shows feedback + shake and increments
      attempts; the correct one collapses the step and advances.
- [ ] Progress bar tracks **real** completed-steps ÷ total (≈20/40/60/80/100%),
      not a fixed 50%.
- [ ] Hints reveal one at a time, increment the counter, and the adaptive nudge
      appears after repeated wrong attempts.
- [ ] Evidence can be added and removed.
- [ ] Score math: each wrong sub-answer costs 3, each hint costs 5, and the score
      never drops below 60.
- [ ] Completing every step (and, for Lab 05, the final assessment) shows the
      completion state (confetti + drawn check + score count-up), the
      **Investigation Summary** (completed steps + evidence), and the outcome copy.

### Per-lab specifics

- [ ] **Lab 01** — try a valid then an invalid login; compare responses; identify
      username enumeration.
- [ ] **Lab 02** — open record 1001, request another id (1002–1004), observe the
      exposure; identify IDOR + the server-side fix.
- [ ] **Lab 03** — run all 7 toolbox tests into the results table (no arbitrary
      input is executed as code); the "unexpected characters" test shows the
      contained reflected-XSS demo; identify the missing control.
- [ ] **Lab 04** — review config by section; findings carry varied severities
      (not all High); rank the worst; view the before/after hardened baseline.
- [ ] **Lab 05** — explore the request/response inspector; complete all 5
      sub-challenges; the combined final assessment gates completion.

## Progress & persistence

- [ ] Completing a lab updates Dashboard, `/progress`, and `/achievements`.
- [ ] "Recommended next" is correct: resume in-progress → first available →
      replay lowest-scoring completed.
- [ ] Skill radar reflects completed labs; weakest-skill hint is sensible.
- [ ] `/progress` shows Strengths / Areas to develop / Recommended next concept
      from real completed-lab performance.
- [ ] Reload the page — progress, scores, and achievements persist (older
      completions keep their original score; new/replayed labs use base-100).
- [ ] "Reset progress" clears everything back to the initial state.

## Safety page

- [ ] "Educational Simulation — No External Targets" banner shows.
- [ ] All five per-lab threat models render with every field populated.

## 404

- [ ] Navigating to an unknown route (or the `notfound` route) shows the 404
      page with working "Go to labs" / "Return home" CTAs.

## Responsiveness

- [ ] No horizontal overflow at 1440 / 1280 / 1024 / 768 / 390 px.
- [ ] Lab workspace stacks cleanly on mobile; tables/cards remain readable.

## Reduced motion

- [ ] With OS "reduce motion" on: no confetti, count-ups/among reveals render
      final state instantly, and no essential content is hidden behind a
      transition.
