# Contributing

## Principles

- **Zero-bloat UI.** Maintain high performance without adding heavy UI/animation/3D libraries. Use the existing lightweight primitives, inline `Icon` component, Canvas 2D, and native CSS.
- **Extend in place.** Preserve the state-based router, the Fast-Refresh-safe
  context split, scoring, and storage keys. Prefer focused edits over rewrites.
- **Additive types.** New `Lab` / state fields should be optional so existing
  persisted data stays valid.

## Conventions

- Components use **named exports** (except `App.tsx`, the default entry).
- Reuse tokens and primitives from `src/components/ui/`; no new arbitrary colour
  values — use the accent helpers (`accentText`, `accentHex`).
- Use **double quotes** for strings containing apostrophes (or escape them);
  an unescaped apostrophe in a single-quoted string breaks the build.
- Keep CSS `@import` statements first in `src/index.css`; put global CSS and
  Tailwind v4 `@theme` customisation there. No unlayered `*` reset.

## Accessibility & motion

- Keyboard-navigable, visible focus states, semantic landmarks and headings.
- Every animation needs a `prefers-reduced-motion` path (there's a hook and a
  CSS guard already).
- Nothing may introduce horizontal overflow at 390px and up.

## Adding content

- New labs: see [`LABS.md`](LABS.md). Include a full `security` block.
- New pages: add a `Route` variant in `src/lib/types.ts`, a `case` in
  `CurrentView` (`src/App.tsx`), and links in the navbar/footer as appropriate.

## Verifying

Run `npm run build` and `npx tsc --noEmit` to verify type safety and build correctness.
