<div align="center">

# 🛡️ Cyber Labs
### *Interactive Cyber Range & Hands-On Application Security Learning Platform*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://security-lab-ivory.vercel.app)
[![React 19](https://img.shields.io/badge/React-19.0-blue?style=for-the-badge&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.0-646CFF?style=for-the-badge&logo=vite)](https://vitejs.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.0-38B2AC?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br />

**Cyber Labs** is a modern, gamified cyber learning platform designed to teach practical application security from a defender's perspective. Featuring five guided, multi-step investigations, learners analyze and patch real vulnerabilities inside **100% safe, client-side browser simulations**.

[**Explore Live Platform**](https://security-lab-ivory.vercel.app) • [**View Lab Catalog**](#-the-five-security-labs) • [**Architecture**](docs/ARCHITECTURE.md) • [**Security Boundary**](docs/SECURITY.md)

</div>

---

## 🌟 Core Highlights

- **🔒 Safe & Isolated Sandbox** — Every target is a fully contained in-memory simulation. Zero external network requests, zero real risk.
- **🎯 Multi-Step Investigations** — Structured `Observe` ➔ `Probe` ➔ `Decide` ➔ `Mitigate` investigation workflow for each vulnerability domain.
- **⚡ Ultra-Lean Performance** — Handcrafted SVG primitives, native Canvas 2D particle systems, and zero heavy runtime libraries. Production bundle weighs **< 120 kB gzip**.
- **📊 Adaptive Skill Radar & Analytics** — Deterministic client-side engine calculates skill profiles, dynamic recommendations, and tiered hint scoring.
- **🏆 Gamification & CTF Flags** — Score tracking (100 base score with attempt/hint deductions), achievement unlocks, and persistent progress via `localStorage`.
- **♿ Accessible & Responsive** — Dark-mode command-center aesthetics, full keyboard navigation, ARIA semantic landmarks, and fluid responsiveness from mobile (390px) to 4K displays.

---

## 🧪 The Five Security Labs

| # | Lab Codename | Vulnerability Domain | Difficulty | Est. Time | Key Learning Objectives |
|:---:|:---|:---|:---:|:---:|:---|
| **01** | **The Weak Front Door** | `Authentication` | Beginner | 15 min | Identify username enumeration, analyze leaking error messages, enforce generic authentication responses & rate limiting. |
| **02** | **Who Owns This Record?** | `Authorization (IDOR/BOLA)` | Beginner | 15 min | Exploit missing object ownership checks via parameter tampering, implement server-side access control validation. |
| **03** | **The Injection Point** | `Input Validation & XSS` | Intermediate | 20 min | Run interactive 7-point input test suites, observe unsanitized reflection, enforce context-aware encoding & strict CSP. |
| **04** | **The Hardened Baseline** | `Security Configuration` | Intermediate | 20 min | Audit live configuration files for `DEBUG` flags, wildcard CORS, and plaintext secrets; align with Principle of Least Privilege. |
| **05** | **The Wire Inspector** | `HTTP Security & Traffic Analysis` | Advanced | 25 min | Inspect raw HTTP requests and responses; analyze `HttpOnly`, `Secure`, `SameSite` flags, HSTS, and header hardening. |

---

## 🖥️ Interactive Simulation Engines

Cyber Labs features four purpose-built simulation engines:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          CYBER LABS ENGINE                             │
├─────────────────┬──────────────────┬─────────────────┬─────────────────┤
│  BrowserFrame   │   TestToolbox    │ ConfigManifest  │  WireInspector  │
│ (Labs 01 & 02)  │    (Lab 03)      │    (Lab 04)     │    (Lab 05)     │
├─────────────────┼──────────────────┼─────────────────┼─────────────────┤
│ • Simulated URL │ • 7 Test Vectors │ • Live Config   │ • Raw Headers   │
│ • State Auth    │ • XSS Reflection │ • CVSS Scoring  │ • Cookie Flags  │
│ • Record Lookup │ • Sanitizer Demo │ • Diff Baseline │ • HSTS & CORS   │
└─────────────────┴──────────────────┴─────────────────┴─────────────────┘
```

---

## 🛠️ Technology Stack

- **Frontend Framework:** [React 19](https://react.dev/) (Hooks, Concurrent Mode)
- **Language:** [TypeScript 5.7+](https://www.typescriptlang.org/) (Strict Mode)
- **Build Tooling:** [Vite 8](https://vitejs.dev/) with Fast HMR
- **Styling & Design System:** [Tailwind CSS v4](https://tailwindcss.com/) (`@tailwindcss/vite`)
- **Graphics & FX:** Native HTML5 Canvas 2D API + CSS Hardware-Accelerated Animations
- **State & Storage:** React Context API + Client-side `localStorage` (`trinetlayer.v1`)

---

## 📂 Repository Structure

```tree
├── docs/                     # Architectural & security documentation
│   ├── ARCHITECTURE.md       # Component hierarchy, state lifecycle, and routing
│   ├── CONTRIBUTING.md       # Development conventions and standards
│   ├── DEPLOYMENT.md         # Deployment configurations & guide
│   ├── LABS.md               # Lab data schema and authoring instructions
│   ├── SECURITY.md           # Safe-simulation boundary & threat models
│   └── TESTING.md            # Manual and integration QA checklist
├── src/
│   ├── components/           # Reusable UI primitives, cards, and navigation
│   │   ├── fx/               # Aurora background, confetti, particle canvases
│   │   ├── hero/             # CyberNetwork canvas & hero landing components
│   │   ├── lab/              # BrowserFrame, HintPanel, CodeEditor, Simulations
│   │   └── ui/               # Handcrafted SVG icons and UI primitives
│   ├── context/              # App context & global state persistence
│   ├── lib/                  # Analytics engine, labs database, and achievements
│   │   ├── achievements.ts   # CTF unlock conditions and badge definitions
│   │   ├── engine.ts         # Deterministic skill scoring & recommendations
│   │   ├── labs.ts           # 5 progressive lab scenarios & step definitions
│   │   ├── storage.ts        # Type-safe localStorage persistence wrapper
│   │   └── types.ts          # Core TypeScript definitions
│   ├── pages/                # Route views (Home, Labs, Workspace, Dashboard, etc.)
│   ├── App.tsx               # Root component & state router
│   ├── index.css             # Tailwind v4 theme tokens & design system
│   └── main.tsx              # Application entrypoint
├── index.html                # HTML5 document shell
├── package.json              # Project dependencies and npm scripts
├── tsconfig.json             # TypeScript configuration
├── vercel.json               # Vercel deployment settings
└── vite.config.ts            # Clean Vite + Tailwind v4 build configuration
```

---

## 🚀 Quick Start / Local Development

### Prerequisites
- **Node.js** `>= 18.0.0`
- **npm** `>= 9.0.0` or **pnpm** `>= 8.0.0`

### 1. Clone the repository
```bash
git clone https://github.com/lakshaysoni22/Security-Lab.git
cd Security-Lab
```

### 2. Install dependencies
```bash
npm install
# or
pnpm install
```

### 3. Start the local development server
```bash
npm run dev
# or
pnpm dev
```
Open [http://localhost:8443](http://localhost:8443) (or the port displayed in your terminal) to view the application.

### 4. Build for production
```bash
npm run build
# Preview production bundle locally:
npm run preview
```

---

## 📜 Documentation Index

Deep dive into the architecture, security mechanisms, and lab extensions:

- 📐 [**Architecture Overview**](docs/ARCHITECTURE.md) — Routing, state lifecycle, and learning engine.
- 🔬 [**Lab Authoring Guide**](docs/LABS.md) — How to add new labs, steps, and challenges.
- 🛡️ [**Security & Threat Models**](docs/SECURITY.md) — Sandbox boundaries and threat modeling.
- 🚢 [**Deployment Guide**](docs/DEPLOYMENT.md) — Static hosting instructions.
- 🧪 [**Testing & QA Guide**](docs/TESTING.md) — Quality assurance test suite.

---

## 🔒 Security & Educational Disclaimer

> **IMPORTANT:** Cyber Labs is designed strictly for educational and defense-training purposes. All targets, credentials, HTTP transactions, and vulnerability flows are simulated within isolated browser memory. This platform does not interact with, target, or attack real-world infrastructure.

---

## 👨‍💻 Author

**Lakshay Soni**
- GitHub: [@lakshaysoni22](https://github.com/lakshaysoni22)
- Project: [Security-Lab](https://github.com/lakshaysoni22/Security-Lab)

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.
