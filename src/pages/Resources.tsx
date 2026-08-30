import { useState } from "react";
import { useApp } from "../context/AppContext";
import { Icon } from "../components/ui/Icon";
import type { IconName } from "../components/ui/Icon";
import {
  Chip,
  GlowCard,
  PremiumButton,
  Reveal,
  SectionHeader,
  accentHex,
  accentText,
  cx,
} from "../components/ui/primitives";

/* ------------------------------------------------------------------ */
/* Foundations — a short primer students read before the modules.      */
/* ------------------------------------------------------------------ */

interface Principle {
  icon: IconName;
  accent: string;
  title: string;
  body: string;
}

const FOUNDATIONS: Principle[] = [
  {
    icon: "shield",
    accent: "cyan",
    title: "The CIA triad",
    body: "Every control you'll study protects one of three things: Confidentiality (only the right people see data), Integrity (data isn't tampered with), and Availability (the system stays up). When you spot a weakness, ask which of the three it breaks.",
  },
  {
    icon: "eye",
    accent: "violet",
    title: "Never trust input",
    body: "Anything that crosses a trust boundary — a form field, a URL, a header, a cookie — is attacker-controlled until proven otherwise. Validate what you accept, and encode what you output. Most web vulnerabilities are a trust assumption that turned out to be false.",
  },
  {
    icon: "lock",
    accent: "primary",
    title: "Least privilege",
    body: "Give every user, process, and request only the access it truly needs — and check that access on the server, on every request. Authentication proves who you are; authorization decides what you're allowed to touch. They are not the same step.",
  },
  {
    icon: "layers",
    accent: "success",
    title: "Defence in depth",
    body: "Assume any single control can fail. Layer independent defences — validation, encoding, authorization, secure config, and monitoring — so that one gap doesn't hand over the whole system. Security is a stack, not a switch.",
  },
];

/* ------------------------------------------------------------------ */
/* Study modules — one long-form lesson per lab domain.                */
/* ------------------------------------------------------------------ */

interface Section {
  heading: string;
  body: string;
}

interface Module {
  labId: string;
  number: string;
  icon: IconName;
  accent: string;
  domain: string;
  title: string;
  readMinutes: number;
  intro: string;
  sections: Section[];
  keyTerms: string[];
}

const MODULES: Module[] = [
  {
    labId: "auth",
    number: "01",
    icon: "fingerprint",
    accent: "cyan",
    domain: "Authentication",
    title: "Proving who a user is",
    readMinutes: 6,
    intro:
      "Authentication answers a single question: is this person who they claim to be? Get it wrong and every other control is built on sand — because the attacker is now trusted as someone else.",
    sections: [
      {
        heading: "The idea",
        body: "A login takes a claimed identity (a username) and a proof (a password, a code, a key) and decides whether they match. The system should reveal as little as possible during this exchange. Every extra detail — a different error message, a slower response, a distinct status code — is a clue an attacker can measure.",
      },
      {
        heading: "How it's exploited",
        body: "In username enumeration, an attacker submits many usernames and watches how the app responds. If a real account returns \"wrong password\" but a fake one returns \"no such user,\" the app has just confirmed which accounts exist. That valid-user list turns a blind guessing game into a focused password-spraying or brute-force campaign.",
      },
      {
        heading: "Worked example",
        body: "Trying to log in as ghost@example returns \"Account not found,\" while admin@example returns \"Incorrect password.\" The wording alone tells the attacker that admin@example is real. Response timing can leak the same fact even when the messages match.",
      },
      {
        heading: "How to defend",
        body: "Return one identical, generic failure for every bad login (\"invalid email or password\"), keep response timing constant, add rate limiting and lockouts, and layer on multi-factor authentication so a leaked password isn't enough on its own.",
      },
    ],
    keyTerms: ["Username enumeration", "Credential stuffing", "MFA", "Rate limiting"],
  },
  {
    labId: "authz",
    number: "02",
    icon: "key",
    accent: "primary",
    domain: "Authorization",
    title: "Deciding what a user may touch",
    readMinutes: 7,
    intro:
      "Authorization runs after authentication: now that we know who you are, what are you allowed to do? Skipping the per-object ownership check is one of the most common — and most damaging — web flaws.",
    sections: [
      {
        heading: "The idea",
        body: "Being logged in is not permission to see everything. For each request, the server must confirm that this specific user owns or is allowed to access this specific record. Trusting an identifier that the client can change is a trap.",
      },
      {
        heading: "How it's exploited",
        body: "In an Insecure Direct Object Reference (IDOR), a URL or request contains an object id such as /records?id=1001. The attacker simply edits it to 1002 and, because the server only checked that they were logged in — not that they owned record 1002 — the other customer's data comes straight back.",
      },
      {
        heading: "Worked example",
        body: "A support agent legitimately opens their own record at id=1001. They change the id to 1002, 1003, 1004 and each request returns a different customer's private details. Nothing was \"hacked\" — the server never asked whether the record belonged to them.",
      },
      {
        heading: "How to defend",
        body: "Authorize every object access on the server, scoped to the current user (\"does this record's owner equal the session user?\"). Prefer unpredictable identifiers, deny by default, and never rely on the UI hiding a button as a security control.",
      },
    ],
    keyTerms: ["IDOR", "Broken object-level authorization", "Least privilege", "Deny by default"],
  },
  {
    labId: "input",
    number: "03",
    icon: "code",
    accent: "violet",
    domain: "Input Validation",
    title: "Treating data as data, not code",
    readMinutes: 7,
    intro:
      "When user input is handled as if it were trusted code or markup, attackers can make the application run their instructions. Validation and output encoding are how you keep data in its lane.",
    sections: [
      {
        heading: "The idea",
        body: "Input arrives as untrusted text. Problems begin when that text is placed somewhere it will be interpreted — HTML, a SQL query, a shell command — without being escaped for that context. The fix is context-aware: validate on the way in, encode on the way out.",
      },
      {
        heading: "How it's exploited",
        body: "In reflected cross-site scripting (XSS), a page echoes user input straight into the HTML. If a comment field accepts <img src=x onerror=alert(1)> and the page renders it as markup, the browser runs the attacker's script — in the victim's session, with the victim's cookies.",
      },
      {
        heading: "Worked example",
        body: "A feedback box reflects whatever you type back onto the page. Plain text is harmless. But a value containing an HTML tag with an event handler executes when the page renders it, because the app inserted the text as HTML instead of escaping it to visible characters.",
      },
      {
        heading: "How to defend",
        body: "Encode output for its exact context (HTML, attribute, URL, JS), validate and normalise input against an allow-list, use frameworks that escape by default, and add a strict Content-Security-Policy as a backstop so injected script has nowhere to run.",
      },
    ],
    keyTerms: ["Reflected XSS", "Output encoding", "Allow-list validation", "Content-Security-Policy"],
  },
  {
    labId: "config",
    number: "04",
    icon: "server",
    accent: "warning",
    domain: "Security Configuration",
    title: "Hardening the defaults",
    readMinutes: 6,
    intro:
      "Most breaches don't need a clever exploit — they walk in through a setting nobody changed. Secure configuration is unglamorous, repetitive, and one of the highest-impact things a defender does.",
    sections: [
      {
        heading: "The idea",
        body: "Software ships with defaults tuned for convenience, not safety: debug mode on, sample credentials, verbose errors, permissive CORS. Left in production, each is a door. Hardening means turning off what you don't need and locking down what you do.",
      },
      {
        heading: "How it's exploited",
        body: "An attacker probes for the easy wins first: a debug endpoint that dumps stack traces and secrets, a default admin/admin login, a wildcard CORS policy that lets any site read your API, or verbose errors that reveal versions and file paths to guide the next step.",
      },
      {
        heading: "Worked example",
        body: "A dashboard left DEBUG=true in production. A single triggered error returns a full stack trace, environment details, and a database hint — a free map of the system's internals, handed to anyone who visits.",
      },
      {
        heading: "How to defend",
        body: "Not every finding is critical — triage by real impact (low / medium / high). Disable debug, rotate default secrets, scope CORS to known origins, return generic errors to users, and audit configuration in CI so drift is caught before it ships.",
      },
    ],
    keyTerms: ["Security misconfiguration", "Hardening", "Secure defaults", "CORS"],
  },
  {
    labId: "http",
    number: "05",
    icon: "globe",
    accent: "success",
    domain: "HTTP Security",
    title: "Reading the request and response",
    readMinutes: 8,
    intro:
      "Every web interaction is an HTTP request and response. Learning to read them — the method, the headers, the cookies, the body — is the skill that ties the previous four domains together.",
    sections: [
      {
        heading: "The idea",
        body: "The request tells you what the client is asking for and what data it controls; the response tells you what the server sent back and how it protects it. Security lives in the details: the method, which values are user-supplied, and which protective headers are present or missing.",
      },
      {
        heading: "How it's exploited",
        body: "If a session cookie lacks the Secure, HttpOnly, and SameSite attributes, it can be stolen over plain HTTP, read by injected script, or replayed cross-site. Missing headers like Strict-Transport-Security or X-Content-Type-Options leave the door open to downgrade and content-sniffing attacks.",
      },
      {
        heading: "Worked example",
        body: "A response sets a session cookie with no flags and omits HSTS. An attacker on the same network downgrades the connection to HTTP and captures the cookie in transit — then replays it to become the victim, no password required.",
      },
      {
        heading: "How to defend",
        body: "Set Secure + HttpOnly + SameSite on session cookies, enforce HTTPS everywhere with HSTS, add X-Content-Type-Options: nosniff and a Content-Security-Policy, and always compare an insecure response against a hardened one to see exactly which header closed the gap.",
      },
    ],
    keyTerms: ["Secure/HttpOnly/SameSite", "HSTS", "Session hijacking", "Security headers"],
  },
];

/* ------------------------------------------------------------------ */
/* Glossary — quick-reference definitions.                             */
/* ------------------------------------------------------------------ */

const GLOSSARY: Array<{ term: string; definition: string }> = [
  { term: "Trust boundary", definition: "The line between code you control and input you don't. Data crossing it must be validated." },
  { term: "Authentication", definition: "Proving identity — confirming a user is who they claim to be." },
  { term: "Authorization", definition: "Deciding what an authenticated user is permitted to access or do." },
  { term: "IDOR", definition: "Insecure Direct Object Reference — reaching another user's data by changing an id the server doesn't re-check." },
  { term: "XSS", definition: "Cross-Site Scripting — running attacker script in a victim's browser via unescaped output." },
  { term: "CSP", definition: "Content-Security-Policy — a response header that restricts where scripts and resources may load from." },
  { term: "Misconfiguration", definition: "Insecure settings left in place — debug mode, default creds, permissive CORS." },
  { term: "HSTS", definition: "HTTP Strict-Transport-Security — forces browsers to use HTTPS, blocking downgrade attacks." },
  { term: "Least privilege", definition: "Granting only the minimum access each user or process needs." },
  { term: "Defence in depth", definition: "Layering independent controls so one failure doesn't compromise the system." },
];

function ModuleCard({ module, isOpen, onToggle }: { module: Module; isOpen: boolean; onToggle: () => void }) {
  const { navigate } = useApp();
  const panelId = `module-panel-${module.labId}`;

  return (
    <GlowCard accent={module.accent} className="overflow-hidden">
      <button
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-controls={panelId}
        className="flex w-full items-center gap-4 p-6 text-left"
      >
        <span
          className={cx("grid h-12 w-12 shrink-0 place-items-center rounded-xl", accentText(module.accent))}
          style={{ background: `color-mix(in srgb, ${accentHex(module.accent)} 12%, transparent)` }}
        >
          <Icon name={module.icon} size={24} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-subtle">
            <span className={accentText(module.accent)}>Module {module.number}</span>
            <span aria-hidden>·</span>
            {module.domain}
          </span>
          <span className="mt-0.5 block text-lg font-semibold text-foreground">{module.title}</span>
        </span>
        <span className="hidden items-center gap-1.5 font-mono text-[11px] text-subtle sm:flex">
          <Icon name="clock" size={13} /> {module.readMinutes} min read
        </span>
        <Icon
          name="chevron-down"
          size={20}
          className={cx("shrink-0 text-subtle transition-transform", isOpen && "rotate-180")}
        />
      </button>

      {isOpen && (
        <div id={panelId} className="animate-fade-slide border-t border-border/70 p-6">
          <p className="text-[15px] leading-relaxed text-muted-foreground">{module.intro}</p>

          <div className="mt-6 space-y-5">
            {module.sections.map((s) => (
              <div key={s.heading}>
                <h4 className={cx("font-mono text-[11px] uppercase tracking-widest", accentText(module.accent))}>
                  {s.heading}
                </h4>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
              </div>
            ))}
          </div>

          <div className="mt-6">
            <div className="font-mono text-[10px] uppercase tracking-widest text-subtle">Key terms</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {module.keyTerms.map((t) => (
                <Chip key={t}>{t}</Chip>
              ))}
            </div>
          </div>

          <PremiumButton
            className="mt-6"
            size="sm"
            variant="outline"
            iconRight="arrow-right"
            onClick={() => navigate({ name: "lab", labId: module.labId })}
          >
            Practise this in Lab {module.number}
          </PremiumButton>
        </div>
      )}
    </GlowCard>
  );
}

export function Resources() {
  const [openId, setOpenId] = useState<string | null>(MODULES[0]?.labId ?? null);

  return (
    <div className="mx-auto max-w-5xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <SectionHeader
        eyebrow="Resources"
        title="The study library"
        description="Read the theory before — or alongside — the labs. Each module explains one security domain in plain language: what it is, how attackers abuse it, a worked example, and how a defender shuts it down."
      />

      {/* Foundations primer */}
      <Reveal className="mt-14">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
          <Icon name="compass" size={14} /> Start here — four ideas behind everything
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {FOUNDATIONS.map((f) => (
            <div key={f.title} className="rounded-2xl border border-border bg-card p-5">
              <div className={cx("flex items-center gap-2", accentText(f.accent))}>
                <Icon name={f.icon} size={18} />
                <h3 className="text-base font-semibold text-foreground">{f.title}</h3>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.body}</p>
            </div>
          ))}
        </div>
      </Reveal>

      {/* Study modules */}
      <Reveal className="mt-12">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
          <Icon name="book" size={14} /> Study modules
        </div>
        <div className="mt-4 space-y-4">
          {MODULES.map((m) => (
            <ModuleCard
              key={m.labId}
              module={m}
              isOpen={openId === m.labId}
              onToggle={() => setOpenId((cur) => (cur === m.labId ? null : m.labId))}
            />
          ))}
        </div>
      </Reveal>

      {/* Glossary */}
      <Reveal className="mt-12">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
          <Icon name="search" size={14} /> Glossary
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {GLOSSARY.map((g) => (
            <div key={g.term} className="rounded-xl border border-border bg-card p-4">
              <dt className="text-sm font-semibold text-foreground">{g.term}</dt>
              <dd className="mt-1 text-sm leading-relaxed text-muted-foreground">{g.definition}</dd>
            </div>
          ))}
        </div>
      </Reveal>
    </div>
  );
}
