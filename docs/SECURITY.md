# Security & Safe-Simulation Model

TrinetLayer is an **educational simulation**. It teaches genuine
application-security techniques, but only ever against fictional targets that run
locally in the browser.

## Hard boundaries

These are non-negotiable properties of the platform:

- **Everything is simulated.** Each target is an in-memory recreation of a
  vulnerable app. There is no backend to attack.
- **No external targets.** The platform never contacts real websites, servers,
  accounts, third-party systems, arbitrary URLs, or arbitrary IP addresses.
- **No unrestricted networking.** Labs do not issue arbitrary network requests;
  every response is scripted and deterministic.
- **No real secrets.** Any credentials, tokens, or session values shown are
  fictional examples for teaching. None are real, stored remotely, or
  transmitted. **No secrets are committed to the repository** (see
  `.env.example`).
- **Fully Offline & Deterministic.** The recommendation/skill/hint engine
  (`src/lib/engine.ts`) is 100% local and deterministic. No external API keys
  are required and the app is fully functional out of the box.

## Lab 03 — the input test toolbox

Lab 03 (Input Validation) is a **deterministic test toolbox**, not an exploit
engine: it runs 7 predefined, hard-coded test inputs (normal, empty, malformed
email, excessive length, unexpected characters, boundary, unexpected type) and
tabulates the result of each. **No user-supplied input is executed as code.** The
single "unexpected characters" test renders one fixed, predefined payload as HTML
to demonstrate reflected XSS — this is deliberate and contained: the render
happens only inside that isolated lab widget, the payload is a constant that never
leaves the page, and no other user can be affected. It is the lesson, not a bug.

## Lab 04 — synthetic configuration only

Lab 04 (Security Configuration) reviews a **fictional, in-memory config manifest**.
No real environment variables, credentials, tokens, keys, or host information are
ever read or displayed; the flagged findings, severities, and the before/after
hardened baseline are all static teaching content.

## Per-lab threat models

Every lab carries a `security` block (`LabSecurity` in `src/lib/types.ts`) that
documents its threat model. These are surfaced on the **Safety** page (full
table) and in the **lab workspace** left column (asset / threat / weakness +
safe boundary).

| Lab | Asset | Threat | Weakness | Remediation |
|-----|-------|--------|----------|-------------|
| 01 Authentication | User accounts | Username enumeration → targeted brute force | Login responses differ for real vs. fake users | Generic failure message, rate limiting, MFA |
| 02 Authorization | Other users' records | IDOR object access | Identity checked, ownership not | Authorize every object access server-side |
| 03 Input Validation | Page integrity & sessions | Reflected XSS | Input reflected as HTML, not escaped | Context-encode output, validate input, strict CSP |
| 04 Security Configuration | Production app & admin access | Exploit of insecure defaults | Dev/factory settings in production | Rotate credentials, disable debug, scope CORS, audit in CI |
| 05 HTTP Security Analysis | Session & data in transit | Session hijacking | Cookie missing Secure/HttpOnly/SameSite; missing headers | Set cookie flags, enforce HSTS, add nosniff |

## Responsible use

Practising these techniques within the labs is the entire point. Applying them to
systems you do not own or have explicit written permission to test is illegal.
The platform exists to train defenders.
