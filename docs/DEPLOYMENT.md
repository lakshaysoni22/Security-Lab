# Deployment

## How this app is served

TrinetLayer is a **static single-page app** built by **Vite**. There is no
server-side runtime, no database, and no external API — all state lives in the
browser's `localStorage`. That makes deployment simple: build once and serve the
static output.

### Local Development

The Vite dev server runs with `pnpm dev` on port 8443 with fast HMR (hot module replacement).

### Anywhere else (static hosting)

```bash
pnpm install
pnpm build      # emits the static site to dist/
pnpm preview    # optional: verify the production build locally
```

Serve the contents of `dist/` from any static host or CDN (e.g. GitHub Pages,
Netlify, Cloudflare Pages, S3 + CloudFront, or any plain web server). Because
routing is state-based (not URL-based), no SPA rewrite rules are required — the
app always boots at `index.html`.

## Not used here

The original brief referenced Next.js, Vercel, and Docker. **None are used.**
This is a Vite + React app with no backend, so those platforms/tooling would add
complexity without benefit. If you later port to a framework with server
rendering, revisit this document.

## Configuration

The app requires **no environment variables** to run. All features work fully
offline and client-side. Never commit real `.env` files, keys, tokens, or secrets.
