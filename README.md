# TrinetLayer Cyber Labs

A hands-on cyber range for learning to think like a defender. Five guided
investigations take you from a weak login all the way to raw HTTP analysis —
every target is a **safe, simulated, in-browser** recreation of a vulnerable
app. Real vulnerabilities, zero real risk.

> **Educational simulation — no external targets.** Nothing here contacts real
> websites, servers, accounts, or IP addresses. See [`docs/SECURITY.md`](docs/SECURITY.md).

## Stack

- **React 19** + **TypeScript** (function components, hooks)
- **Vite** (dev server + esbuild bundling)
- **Tailwind CSS v4** via `@tailwindcss/vite` (tokens live in `src/index.css`)
- **Ultra-lean UI** — zero heavy runtime UI dependencies. Icons are handcrafted SVG primitives, interactive canvases use the native 2D Canvas API, and motion is hardware-accelerated with CSS and `IntersectionObserver`. This keeps the production bundle under 120kB gzip.

## Getting Started

```bash
pnpm install # or npm install
pnpm dev     # start the Vite dev server
pnpm build   # production build
pnpm preview # preview production bundle
```


## Features

- **Landing page** — cinematic hero, learning-path timeline, skill matrix,
  simulation model, FAQ, and CTA.
- **Five progressive labs** — authentication, authorization (IDOR), input
  validation (XSS), security configuration, and HTTP security analysis.
- **Lab engine** — one investigation loop (mission → simulate → evidence →
  prove) reused across every lab, with tiered hints and answer validation.
- **Multi-step investigations** — each lab is an observe → probe → decide sequence
  (Lab 05 adds a combined final assessment), with real per-step progress.
- **Scoring** — standardized base of 100 per lab, −3 per wrong sub-answer attempt
  and −5 per hint, floored at 60; persisted per lab.
- **Dashboard / Progress / Achievements** — overall ring, skill radar,
  recommended next lab, per-lab breakdown, and an achievement gallery.
- **Safety page** — the safe-simulation model plus a per-lab threat model.
- **Adaptive Learning Engine** — `src/lib/engine.ts` computes recommendations,
  skill profiles, and adaptive hint ordering deterministically based on learner progress.
- **Local persistence** — progress is saved to `localStorage`
  (`trinetlayer.v1`); reset it from the dashboard.
- **Accessible + responsive** — keyboard nav, focus states, semantic landmarks,
  `prefers-reduced-motion` fallbacks, and no horizontal overflow down to 390px.

## The five labs

| # | Codename | Category | Difficulty | Teaches |
|---|----------|----------|------------|---------|
| 01 | Authentication | Identity | Beginner | Username enumeration |
| 02 | Authorization | Access Control | Beginner | IDOR / missing ownership checks |
| 03 | Input Validation | Injection | Intermediate | Reflected XSS |
| 04 | Security Configuration | Hardening | Intermediate | Insecure defaults & secrets |
| 05 | HTTP Security Analysis | Traffic Analysis | Advanced | Cookie flags & security headers |

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — structure, routing, state, engine.
- [`docs/LABS.md`](docs/LABS.md) — the lab data model and how to add a lab.
- [`docs/SECURITY.md`](docs/SECURITY.md) — safe-simulation boundary + threat models.
- [`docs/TESTING.md`](docs/TESTING.md) — manual QA checklist.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — how this app is served.
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — conventions and guardrails.

## License / use

Educational use only.
