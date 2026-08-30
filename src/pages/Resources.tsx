import { useState, useMemo } from "react";
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
/* Core Security Principles (Foundations)                             */
/* ------------------------------------------------------------------ */

interface Principle {
  icon: IconName;
  accent: string;
  title: string;
  subtitle: string;
  body: string;
}

const FOUNDATIONS: Principle[] = [
  {
    icon: "shield",
    accent: "cyan",
    title: "The CIA Triad",
    subtitle: "Confidentiality, Integrity, Availability",
    body: "Every security control protects one or more pillars: Confidentiality (only authorized parties view data), Integrity (data is accurate and un-tampered), and Availability (systems remain accessible to authorized users when needed).",
  },
  {
    icon: "eye",
    accent: "violet",
    title: "Never Trust Client Input",
    subtitle: "Assume all input is hostile",
    body: "Anything originating outside your server boundary — query strings, POST bodies, headers, cookies, API payloads, and even file names — is attacker-controllable. Validate strictly on the server using allow-lists, not block-lists.",
  },
  {
    icon: "lock",
    accent: "primary",
    title: "Principle of Least Privilege",
    subtitle: "Minimum necessary permissions",
    body: "Users, applications, and system processes should only have access to the exact resources required to perform their intended function. Granting broad 'Admin' or root privileges creates catastrophic single points of failure.",
  },
  {
    icon: "layers",
    accent: "success",
    title: "Defence in Depth",
    subtitle: "Layered, redundant safeguards",
    body: "Assume individual controls will eventually fail. By combining network firewalls, strict access controls, input validation, context-aware encoding, secure headers, and runtime monitoring, a breach in one layer is stopped by the next.",
  },
  {
    icon: "server",
    accent: "warning",
    title: "Zero Trust Architecture",
    subtitle: "Never trust, always verify",
    body: "Traditional perimeter security assumes everything inside the network is safe. Zero Trust treats all requests as potentially hostile, requiring mutual authentication, per-request authorization, and micro-segmentation at every hop.",
  },
  {
    icon: "zap",
    accent: "cyan",
    title: "Fail Securely",
    subtitle: "Safe error handling",
    body: "When exceptions, database disconnects, or validation checks fail, the system must default to the most secure state: access denied, generic error messages, and no debug traces exposed to end users.",
  },
];

/* ------------------------------------------------------------------ */
/* Deep-Dive Study Modules with Real Case Studies & Attack Blueprints */
/* ------------------------------------------------------------------ */

interface Section {
  heading: string;
  body: string;
  codeSnippet?: string;
}

interface Module {
  labId: string;
  number: string;
  icon: IconName;
  accent: string;
  domain: string;
  title: string;
  readMinutes: number;
  owaspRef: string;
  cweRef: string;
  intro: string;
  realWorldBreach: {
    target: string;
    year: string;
    impact: string;
    lesson: string;
  };
  sections: Section[];
  defenseChecklist: string[];
  keyTerms: string[];
}

const MODULES: Module[] = [
  {
    labId: "auth",
    number: "01",
    icon: "fingerprint",
    accent: "cyan",
    domain: "Authentication",
    title: "Proving Identity & Preventing Account Takeover",
    readMinutes: 8,
    owaspRef: "A07:2021 - Identification & Authentication Failures",
    cweRef: "CWE-287 / CWE-204",
    intro:
      "Authentication is the gatekeeper of your entire application. When authentication mechanisms leak information or fail to enforce rate limits, attackers map user bases and execute automated credential stuffing attacks.",
    realWorldBreach: {
      target: "Major Web Services & Streaming Platforms",
      year: "Recurring Industry Threat",
      impact: "Billions of leaked password records tested through automated botnets against portals leaking account validity.",
      lesson: "Single-generic failure responses, CAPTCHA on anomalous traffic, and mandatory MFA eliminate 99.9% of automated attacks.",
    },
    sections: [
      {
        heading: "The Core Mechanism & Trust Boundary",
        body: "A login endpoint accepts a claim (username/email) and verification secret (password/token). The application must evaluate both without giving away which part of the pair failed. If the server reveals 'User not found' vs 'Incorrect password', it hands attackers an active directory list of valid accounts.",
      },
      {
        heading: "Attack Anatomy: Username Enumeration & Password Spraying",
        body: "Attackers script HTTP requests with dictionary lists of employee names. By analyzing status codes, text variations, or microsecond timing differentials (response times), they filter thousands of usernames down to a verified list of active accounts for targeted brute-forcing.",
        codeSnippet: `// ❌ INSECURE: Leaks account existence\nif (!userExists(email)) {\n  return res.status(404).json({ error: "No account found with this email" });\n}\nif (!verifyPassword(password, user.hash)) {\n  return res.status(401).json({ error: "Invalid password for user" });\n}\n\n// ✅ SECURE: Identical generic response with constant-time check\nconst user = findUserOrDummy(email);\nconst isValid = verifyPasswordConstantTime(password, user.hash);\nif (!user.isReal || !isValid) {\n  return res.status(401).json({ error: "Invalid email or password" });\n}`,
      },
      {
        heading: "Session Lifecycle & Replay Prevention",
        body: "Upon authentication, session identifiers must be generated with cryptographically secure random number generators (CSPRNG) with at least 128 bits of entropy. Sessions must immediately regenerate upon privilege changes (preventing Session Fixation) and terminate on explicit logout or inactivity timeouts.",
      },
    ],
    defenseChecklist: [
      "Return uniform error responses: 'Invalid email or password' for all failure modes.",
      "Implement adaptive rate limiting (e.g. 5 failed attempts per IP/user triggers exponential backoff or CAPTCHA).",
      "Enforce modern multi-factor authentication (TOTP RFC 6238 or FIDO2/WebAuthn hardware keys).",
      "Store passwords using modern memory-hard key derivation functions (Argon2id, bcrypt cost >= 12, or scrypt).",
      "Regenerate session tokens upon successful login to prevent session fixation attacks.",
    ],
    keyTerms: ["Username Enumeration", "Credential Stuffing", "MFA / WebAuthn", "Argon2id / bcrypt", "Rate Limiting", "CSPRNG"],
  },
  {
    labId: "authz",
    number: "02",
    icon: "key",
    accent: "primary",
    domain: "Authorization",
    title: "Broken Object-Level Authorization (IDOR / BOLA)",
    readMinutes: 9,
    owaspRef: "A01:2021 - Broken Access Control (Rank #1)",
    cweRef: "CWE-639 / CWE-284 / CWE-285",
    intro:
      "Broken Access Control is currently the #1 vulnerability on the OWASP Top 10. Insecure Direct Object References (IDOR) occur when an application relies on client-provided IDs to fetch records without validating that the authenticated session actually owns that resource.",
    realWorldBreach: {
      target: "Telecommunications & Healthcare Portals",
      year: "2022 - 2024",
      impact: "Over 10 million subscriber records exposed through sequential customer_id parameters in unauthenticated API endpoints.",
      lesson: "Obscurity is not security. Every database query fetching user data MUST include a tenant/user ID predicate bound to the verified session.",
    },
    sections: [
      {
        heading: "Why IDOR Flaws Happen",
        body: "Developers often check if a user is logged in (Authentication) but forget to check if they have permission to access the specific database row (Authorization). When endpoints look like GET /api/documents?id=4920, incrementing the integer to 4921 fetches another user's document.",
      },
      {
        heading: "Horizontal vs. Vertical Privilege Escalation",
        body: "Horizontal Escalation: A standard user accesses data belonging to another standard user with identical privileges (e.g., viewing another customer's bank statement). Vertical Escalation: A regular user accesses administrative functions or resources (e.g., executing /api/admin/deleteUser without admin role).",
        codeSnippet: `// ❌ INSECURE: Relies entirely on client-supplied ID\napp.get('/api/invoice/:invoiceId', authenticateUser, async (req, res) => {\n  const invoice = await db.invoices.findById(req.params.invoiceId);\n  res.json(invoice); // Anyone logged in can see ANY invoice!\n});\n\n// ✅ SECURE: Scoped to authenticated session ownership\napp.get('/api/invoice/:invoiceId', authenticateUser, async (req, res) => {\n  const invoice = await db.invoices.findOne({\n    _id: req.params.invoiceId,\n    userId: req.user.id // Enforced database-level boundary\n  });\n  if (!invoice) return res.status(404).json({ error: "Invoice not found" });\n  res.json(invoice);\n});`,
      },
      {
        heading: "UUIDs vs. Server-Side Access Control",
        body: "Replacing sequential IDs (1, 2, 3) with UUIDv4 strings makes guessing harder, but it is NOT an access control mechanism. If a UUID leaks in a referrer header, logs, or shared link, an unprotected endpoint will still expose the record. Robust authorization checks must always validate ownership.",
      },
    ],
    defenseChecklist: [
      "Bind all CRUD database queries to `session.userId` or enforce strict Role-Based Access Control (RBAC).",
      "Adopt a 'Deny by Default' policy in middleware and API gateways.",
      "Use cryptographically random UUIDv4 or nano IDs instead of predictable sequential integer IDs.",
      "Implement automated API security testing for authorization bypass across all tenant boundaries.",
      "Disable directory listing and protect administrative routes with strict role guards.",
    ],
    keyTerms: ["IDOR / BOLA", "Horizontal Escalation", "Vertical Escalation", "RBAC / ABAC", "Deny by Default", "UUIDv4"],
  },
  {
    labId: "input",
    number: "03",
    icon: "code",
    accent: "violet",
    domain: "Input Validation",
    title: "Injection Prevention & Context-Aware Output Encoding",
    readMinutes: 10,
    owaspRef: "A03:2021 - Injection (XSS, SQLi, Command Injection)",
    cweRef: "CWE-79 (XSS) / CWE-89 (SQLi) / CWE-78 (OS Cmd)",
    intro:
      "Injection occurs when untrusted user data is concatenated directly into interpreters (HTML, SQL, Shell, LDAP) without proper sanitization or context-aware encoding, tricking the parser into executing attacker instructions.",
    realWorldBreach: {
      target: "British Airways & Ticketmaster (Magecart)",
      year: "2018",
      impact: "Over 380,000 payment card records stolen by injecting malicious JavaScript scripts that exfiltrated credit card keystrokes.",
      lesson: "Strict Content-Security-Policy (CSP), context-aware escaping, and Subresource Integrity (SRI) prevent malicious script execution.",
    },
    sections: [
      {
        heading: "The Root Cause of Injection",
        body: "Computers execute commands by parsing data streams. When code (instructions) and data (user inputs) are mixed without explicit delimiters, an attacker can input special characters (', \", <script>, ;) that change how the interpreter understands the remainder of the sentence.",
      },
      {
        heading: "The Three Types of Cross-Site Scripting (XSS)",
        body: "1. Reflected XSS: Malicious payload in a URL/search query is immediately echoed back in the HTML response. 2. Stored XSS: Injected script is saved in the database (e.g. comments, profile names) and served to all future visitors. 3. DOM-based XSS: Vulnerability exists purely in client-side JavaScript (e.g., using innerHTML, eval, or document.write with user input).",
        codeSnippet: `// ❌ INSECURE: Direct HTML injection (DOM XSS)\ndocument.getElementById('greeting').innerHTML = 'Hello, ' + userInput;\n\n// ✅ SECURE: Safe text node assignment (auto-escaped by browser)\ndocument.getElementById('greeting').textContent = 'Hello, ' + userInput;\n\n// ❌ INSECURE: SQL String Concatenation\nconst query = "SELECT * FROM users WHERE email = '" + req.body.email + "'";\n\n// ✅ SECURE: Parameterized Prepared Statements (DB treats input strictly as data)\nconst query = "SELECT * FROM users WHERE email = ?";\ndb.query(query, [req.body.email]);`,
      },
      {
        heading: "Context-Aware Encoding vs. Sanitization",
        body: "Escaping must match where data is placed: HTML Body (`&` to `&amp;`, `<` to `&lt;`), HTML Attributes (quote escaping), JavaScript Variables (`\\xHH` hex encoding), or URLs (`encodeURIComponent`). Modern UI frameworks (React, Vue, Angular) auto-escape inside template bindings.",
      },
    ],
    defenseChecklist: [
      "Always use Parameterized Queries / Prepared Statements or Object-Relational Mappers (ORMs) for SQL.",
      "Use safe DOM APIs: `.textContent` and `.setAttribute()` instead of `.innerHTML` or `eval()`.",
      "Deploy a strict `Content-Security-Policy` header to prevent execution of unauthorized inline scripts.",
      "Validate input using strict allow-lists (regex, schemas, type checks) before processing.",
      "Set `HttpOnly` on sensitive session cookies so XSS cannot access `document.cookie`.",
    ],
    keyTerms: ["Reflected XSS", "Stored XSS", "DOM XSS", "Prepared Statements", "Context-Aware Encoding", "Content Security Policy"],
  },
  {
    labId: "config",
    number: "04",
    icon: "server",
    accent: "warning",
    domain: "Security Configuration",
    title: "Server Hardening & Secure Default Baselines",
    readMinutes: 8,
    owaspRef: "A05:2021 - Security Misconfiguration",
    cweRef: "CWE-16 / CWE-200 / CWE-942",
    intro:
      "Most real-world breaches don't require zero-day exploits. They happen because production environments leave debugging enabled, use default credentials, expose internal stack traces, or configure overly permissive CORS policies.",
    realWorldBreach: {
      target: "Equifax",
      year: "2017",
      impact: "147 million consumers affected due to unpatched Apache Struts configuration and internal network segmentation gaps.",
      lesson: "Automated vulnerability scanning, hardened baseline configurations, and removing default accounts are mandatory.",
    },
    sections: [
      {
        heading: "The Danger of Development Defaults in Production",
        body: "Frameworks (Django, Express, Spring, Laravel) ship with defaults optimized for local developer convenience: verbose debug pages, stack traces displaying environment variables/passwords, and wildcard CORS headers. If these reach production, attackers gain instant reconnaissance.",
      },
      {
        heading: "Cross-Origin Resource Sharing (CORS) Misconfiguration",
        body: "CORS allows web apps to request resources from a different origin. Setting `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true` is an invalid combination in browsers, but echoing the incoming `Origin` header dynamically allows any malicious website to read authenticated user responses.",
        codeSnippet: `// ❌ INSECURE: Echoing arbitrary origin with credentials\napp.use((req, res, next) => {\n  res.header("Access-Control-Allow-Origin", req.headers.origin); // Dangerous!\n  res.header("Access-Control-Allow-Credentials", "true");\n  next();\n});\n\n// ✅ SECURE: Strict allow-list of trusted production domains\nconst TRUSTED_ORIGINS = new Set(["https://portal.company.com", "https://api.company.com"]);\napp.use((req, res, next) => {\n  const origin = req.headers.origin;\n  if (TRUSTED_ORIGINS.has(origin)) {\n    res.header("Access-Control-Allow-Origin", origin);\n    res.header("Access-Control-Allow-Credentials", "true");\n  }\n  next();\n});`,
      },
      {
        heading: "Hardening Principles & CIS Benchmarks",
        body: "Systems should follow Center for Internet Security (CIS) benchmarks: remove all unnecessary packages/services, disable directory listing, change all default administrative passwords, and ensure least-privilege file permissions on configuration files.",
      },
    ],
    defenseChecklist: [
      "Explicitly set `NODE_ENV=production` / `DEBUG=false` across all staging and production deployments.",
      "Disable server version banners (`Server`, `X-Powered-By: Express`) to prevent automated version reconnaissance.",
      "Restrict CORS to explicit, trusted domain origins — never echo arbitrary `Origin` headers with credentials.",
      "Store secrets in environment variables or cloud secret managers (AWS Secrets Manager, HashiCorp Vault), never in git.",
      "Disable directory indexing on web servers (Nginx `autoindex off`, Apache `Options -Indexes`).",
    ],
    keyTerms: ["CIS Benchmarks", "Hardening", "CORS Misconfiguration", "Information Disclosure", "Secrets Management", "Least Functionality"],
  },
  {
    labId: "http",
    number: "05",
    icon: "globe",
    accent: "success",
    domain: "HTTP & Network Security",
    title: "Traffic Analysis, Security Headers & Cookie Flags",
    readMinutes: 9,
    owaspRef: "A05:2021 - Security Misconfiguration / Transport Layer Security",
    cweRef: "CWE-614 / CWE-1004 / CWE-319",
    intro:
      "HTTP is the fundamental transport protocol of the modern web. Securing the communication channel requires enforcing HTTPS, protecting session tokens with strict cookie attributes, and instructing browsers to activate modern security mitigations through HTTP response headers.",
    realWorldBreach: {
      target: "Public Wi-Fi & Unsecured Corporate Networks",
      year: "Ongoing Threat",
      impact: "Man-in-the-Middle (MitM) session hijacking by sniffing cleartext cookies over non-HSTS HTTP connections.",
      lesson: "Strict HSTS preloading and triple-flagged cookies (Secure, HttpOnly, SameSite=Strict) prevent transport interception.",
    },
    sections: [
      {
        heading: "The Essential Security Headers",
        body: "HTTP response headers instruct modern browsers to enforce strict security boundaries. Missing headers leave users vulnerable to clickjacking, MIME-type sniffing, cross-site leaks, and SSL stripping attacks.",
        codeSnippet: `// Recommended Production HTTP Response Headers:\nStrict-Transport-Security: max-age=31536000; includeSubDomains; preload\nContent-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'\nX-Content-Type-Options: nosniff\nX-Frame-Options: DENY\nReferrer-Policy: strict-origin-when-cross-origin\nPermissions-Policy: camera=(), microphone=(), geolocation=()`,
      },
      {
        heading: "The Cookie Security Trio: Secure, HttpOnly, SameSite",
        body: "`Secure`: Ensures the cookie is ONLY transmitted over encrypted HTTPS connections, preventing plaintext sniffing. `HttpOnly`: Blocks client-side JavaScript (`document.cookie`) from accessing the token, mitigating XSS session theft. `SameSite`: Controls whether cookies are sent with cross-site requests, mitigating Cross-Site Request Forgery (CSRF).",
      },
      {
        heading: "Clickjacking & Frame Busting",
        body: "Clickjacking involves embedding a target website inside an invisible `<iframe>` on a malicious site, tricking the user into clicking buttons (e.g., 'Confirm Transfer'). Setting `X-Frame-Options: DENY` or CSP `frame-ancestors 'none'` completely blocks third-party iframe embedding.",
      },
    ],
    defenseChecklist: [
      "Enforce HTTPS with `Strict-Transport-Security` (HSTS) with at least 1-year max-age and subdomains included.",
      "Always set `Secure`, `HttpOnly`, and `SameSite=Lax` or `SameSite=Strict` on session cookies.",
      "Add `X-Content-Type-Options: nosniff` to prevent browsers from interpreting non-script files as scripts.",
      "Set `X-Frame-Options: DENY` or CSP `frame-ancestors 'none'` to eliminate clickjacking risks.",
      "Enforce minimal `Referrer-Policy` (e.g. `strict-origin-when-cross-origin`) to prevent sensitive query tokens from leaking.",
    ],
    keyTerms: ["HSTS", "SameSite Cookies", "HttpOnly", "Clickjacking (X-Frame-Options)", "MIME Sniffing", "CSRF Protection"],
  },
];

/* ------------------------------------------------------------------ */
/* Quick Reference Cheat Sheets (Tabbed / Filterable)                 */
/* ------------------------------------------------------------------ */

interface CheatSheetItem {
  key: string;
  badge?: string;
  badgeType?: "good" | "warn" | "neutral";
  desc: string;
  recommendedValue?: string;
}

interface CheatSheetCategory {
  id: string;
  title: string;
  icon: IconName;
  items: CheatSheetItem[];
}

const CHEAT_SHEETS: CheatSheetCategory[] = [
  {
    id: "headers",
    title: "Essential Security Headers",
    icon: "layers",
    items: [
      {
        key: "Strict-Transport-Security (HSTS)",
        badge: "Mandatory",
        badgeType: "good",
        desc: "Forces the browser to always connect via HTTPS, preventing SSL stripping and downgrade attacks.",
        recommendedValue: "max-age=31536000; includeSubDomains; preload",
      },
      {
        key: "Content-Security-Policy (CSP)",
        badge: "Critical",
        badgeType: "good",
        desc: "Restricts which scripts, styles, images, and fonts are permitted to load and execute.",
        recommendedValue: "default-src 'self'; script-src 'self'; object-src 'none';",
      },
      {
        key: "X-Content-Type-Options",
        badge: "Essential",
        badgeType: "good",
        desc: "Stops browsers from MIME-sniffing a response away from the declared content-type.",
        recommendedValue: "nosniff",
      },
      {
        key: "X-Frame-Options",
        badge: "Essential",
        badgeType: "good",
        desc: "Prevents your pages from being embedded in iframes on malicious sites, stopping clickjacking.",
        recommendedValue: "DENY (or SAMEORIGIN)",
      },
      {
        key: "Referrer-Policy",
        badge: "Privacy",
        badgeType: "neutral",
        desc: "Controls how much referrer information (URL parameters, paths) is included with outgoing requests.",
        recommendedValue: "strict-origin-when-cross-origin",
      },
      {
        key: "Permissions-Policy",
        badge: "Hardening",
        badgeType: "neutral",
        desc: "Disables browser hardware features (camera, microphone, geolocation) by default.",
        recommendedValue: "camera=(), microphone=(), geolocation=()",
      },
    ],
  },
  {
    id: "cookies",
    title: "Cookie Security Attributes",
    icon: "lock",
    items: [
      {
        key: "Secure Flag",
        badge: "HTTPS Only",
        badgeType: "good",
        desc: "Ensures the browser never transmits the cookie over unencrypted plain HTTP connections.",
        recommendedValue: "Set-Cookie: session=...; Secure",
      },
      {
        key: "HttpOnly Flag",
        badge: "XSS Defense",
        badgeType: "good",
        desc: "Hides the cookie from JavaScript (document.cookie), making it immune to theft via XSS injection.",
        recommendedValue: "Set-Cookie: session=...; HttpOnly",
      },
      {
        key: "SameSite=Lax",
        badge: "Default CSRF Guard",
        badgeType: "good",
        desc: "Cookies withheld on cross-site subrequests (images, forms) but sent on top-level incoming navigations.",
        recommendedValue: "Set-Cookie: session=...; SameSite=Lax",
      },
      {
        key: "SameSite=Strict",
        badge: "Max CSRF Guard",
        badgeType: "good",
        desc: "Cookie is strictly withheld on ALL cross-site requests, including direct link clicks from external sites.",
        recommendedValue: "Set-Cookie: session=...; SameSite=Strict",
      },
      {
        key: "__Host- Prefix",
        badge: "Domain Lock",
        badgeType: "neutral",
        desc: "Enforces that the cookie has Secure flag, Path=/, and cannot be overwritten by subdomains.",
        recommendedValue: "Set-Cookie: __Host-id=...; Secure; Path=/; HttpOnly",
      },
    ],
  },
  {
    id: "status-codes",
    title: "HTTP Status Codes & Security Meaning",
    icon: "activity",
    items: [
      {
        key: "200 OK",
        desc: "Request succeeded. Ensure sensitive responses include Cache-Control: no-store.",
      },
      {
        key: "301 Moved Permanently",
        desc: "Permanent redirect. Used to redirect HTTP traffic to HTTPS (alongside HSTS).",
      },
      {
        key: "400 Bad Request",
        desc: "Malformed request syntax. Return generic validation errors, never internal stack traces.",
      },
      {
        key: "401 Unauthorized",
        desc: "Authentication required or credentials invalid. (Meaning: 'You are not logged in').",
      },
      {
        key: "403 Forbidden",
        desc: "Authenticated, but access denied by authorization policy. (Meaning: 'You cannot touch this').",
      },
      {
        key: "404 Not Found",
        desc: "Resource does not exist or hidden for authorization defense (preventing IDOR enumeration).",
      },
      {
        key: "429 Too Many Requests",
        desc: "Rate limit triggered. Essential defense against brute-force and DDoS scraping.",
      },
      {
        key: "500 Internal Server Error",
        desc: "Uncaught backend exception. Critical: Must NEVER expose file paths, SQL errors, or stack traces.",
      },
    ],
  },
  {
    id: "owasp-top10",
    title: "OWASP Top 10 (2021 Reference)",
    icon: "shield",
    items: [
      { key: "A01: Broken Access Control", desc: "Failures enforcing authorization rules; users acting outside their intended permissions (IDOR, BOLA)." },
      { key: "A02: Cryptographic Failures", desc: "Exposure of sensitive data due to weak algorithms (MD5, SHA1), missing encryption in transit or at rest." },
      { key: "A03: Injection", desc: "Hostile data sent to an interpreter (SQL, XSS, OS Command, LDAP, NoSQL) executed as commands." },
      { key: "A04: Insecure Design", desc: "Flaws in architecture, threat modeling, and business logic that cannot be fixed by coding alone." },
      { key: "A05: Security Misconfiguration", desc: "Unpatched flaws, default accounts, debug mode enabled, open cloud storage, permissive CORS." },
      { key: "A06: Vulnerable & Outdated Components", desc: "Running libraries, frameworks, or dependencies with known public vulnerabilities (CVEs)." },
      { key: "A07: Identification & Auth Failures", desc: "Permitting credential stuffing, weak password requirements, missing brute-force protection, missing MFA." },
      { key: "A08: Software & Data Integrity Failures", desc: "Unverified software updates, untrusted CI/CD pipelines, insecure deserialization flaws." },
      { key: "A09: Security Logging & Monitoring Failures", desc: "Failures to log security events, audit breaches, or detect active intrusions in real-time." },
      { key: "A10: Server-Side Request Forgery (SSRF)", desc: "Server tricked into fetching a remote resource (e.g. cloud metadata 169.254.169.254) on behalf of attacker." },
    ],
  },
];

/* ------------------------------------------------------------------ */
/* Recommended Free Tools & Practice Resources                        */
/* ------------------------------------------------------------------ */

interface LearningResource {
  title: string;
  category: string;
  url: string;
  desc: string;
  icon: IconName;
}

const EXTERNAL_RESOURCES: LearningResource[] = [
  {
    title: "OWASP Cheat Sheet Series",
    category: "Official Reference",
    url: "https://cheatsheetseries.owasp.org/",
    desc: "Concise security guidance written by top security architects covering authentication, REST APIs, headers, and crypto.",
    icon: "shield",
  },
  {
    title: "PortSwigger Web Security Academy",
    category: "Hands-on Practice",
    url: "https://portswigger.net/web-security",
    desc: "The gold standard for interactive web security labs covering SQLi, XSS, CSRF, SSRF, OAuth, and API security for free.",
    icon: "terminal",
  },
  {
    title: "CyberChef — The Cyber Swiss Army Knife",
    category: "Security Utility",
    url: "https://gchq.github.io/CyberChef/",
    desc: "GCHQ's browser tool for decoding Base64, Hex, URL encoding, parsing JWTs, hashing, and inspecting payloads in real-time.",
    icon: "tool",
  },
  {
    title: "Mozilla Web Security Guidelines",
    category: "Standards & Hardening",
    url: "https://infosec.mozilla.org/guidelines/web_security",
    desc: "Production-ready guidelines for HTTP security headers, TLS ciphers, cookie configurations, and CSP directives.",
    icon: "globe",
  },
  {
    title: "NVD (National Vulnerability Database)",
    category: "CVE Research",
    url: "https://nvd.nist.gov/",
    desc: "U.S. government repository of standards-based vulnerability management data using the Common Vulnerabilities and Exposures (CVE) system.",
    icon: "database",
  },
  {
    title: "NIST Cybersecurity Framework (CSF)",
    category: "Framework & Policy",
    url: "https://www.nist.gov/cyberframework",
    desc: "Global benchmark framework for organizational risk assessment: Identify, Protect, Detect, Respond, and Recover.",
    icon: "layers",
  },
];

/* ------------------------------------------------------------------ */
/* Expanded Cybersecurity Glossary (30+ Terms)                        */
/* ------------------------------------------------------------------ */

interface GlossaryEntry {
  term: string;
  category: "Fundamentals" | "Attacks" | "Defense" | "Protocols" | "Crypto";
  definition: string;
}

const GLOSSARY: GlossaryEntry[] = [
  { term: "CIA Triad", category: "Fundamentals", definition: "The three foundational pillars of information security: Confidentiality, Integrity, and Availability." },
  { term: "Trust Boundary", category: "Fundamentals", definition: "The perimeter separating trusted internal code from untrusted external data. Any data crossing it must be validated." },
  { term: "Authentication (AuthN)", category: "Fundamentals", definition: "The process of verifying identity — answering 'Who are you?' using passwords, biometrics, or keys." },
  { term: "Authorization (AuthZ)", category: "Fundamentals", definition: "The process of verifying permissions — answering 'What are you allowed to access or perform?'" },
  { term: "Least Privilege", category: "Defense", definition: "Security model of granting users and processes only the absolute minimum permissions required for their tasks." },
  { term: "Defense in Depth", category: "Defense", definition: "Implementing multiple redundant defensive layers so that the failure of any single safeguard does not cause a total compromise." },
  { term: "Zero Trust", category: "Defense", definition: "A security architecture operating on the principle 'Never trust, always verify', requiring continuous authentication at every layer." },
  { term: "IDOR / BOLA", category: "Attacks", definition: "Insecure Direct Object Reference / Broken Object Level Authorization: manipulating IDs (e.g. ?id=102) to access unauthorized records." },
  { term: "Cross-Site Scripting (XSS)", category: "Attacks", definition: "Injecting malicious JavaScript into web applications which executes in the victim browser session (Reflected, Stored, or DOM)." },
  { term: "SQL Injection (SQLi)", category: "Attacks", definition: "Injecting database commands through untrusted inputs when queries fail to use prepared parameterized statements." },
  { term: "Cross-Site Request Forgery (CSRF)", category: "Attacks", definition: "Tricking a victim browser into making unwanted authenticated state-changing actions on a trusted site." },
  { term: "Server-Side Request Forgery (SSRF)", category: "Attacks", definition: "Abusing server functionality to force the backend to send requests to internal resources (e.g., AWS metadata 169.254.169.254)." },
  { term: "Credential Stuffing", category: "Attacks", definition: "Automated bot attacks testing stolen username/password dumps from previous breaches against target web services." },
  { term: "Brute Force Attack", category: "Attacks", definition: "Systematically trying every possible combination of passwords, keys, or IDs until finding a match." },
  { term: "Clickjacking", category: "Attacks", definition: "Tricking users into clicking malicious buttons by embedding transparent iframe overlays over trusted pages (stopped by X-Frame-Options: DENY)." },
  { term: "Man-in-the-Middle (MitM)", category: "Attacks", definition: "An attacker secretly intercepting and altering communications between two parties who believe they are directly talking." },
  { term: "Session Fixation", category: "Attacks", definition: "An attack where an adversary sets a victim's session ID before authentication and abuses it once the victim logs in." },
  { term: "Content Security Policy (CSP)", category: "Defense", definition: "An HTTP response header defining approved sources of executable scripts, stylesheets, and assets to mitigate XSS." },
  { term: "HSTS", category: "Protocols", definition: "HTTP Strict Transport Security: response header enforcing HTTPS-only connections and blocking SSL-stripping downgrades." },
  { term: "SameSite Cookie", category: "Protocols", definition: "Cookie attribute (Strict/Lax/None) controlling whether the cookie is sent along with cross-origin requests, blocking CSRF." },
  { term: "HttpOnly Cookie", category: "Defense", definition: "A cookie attribute preventing client-side scripts from reading session tokens via document.cookie, stopping XSS theft." },
  { term: "CORS", category: "Protocols", definition: "Cross-Origin Resource Sharing: mechanism using HTTP headers to tell browsers whether a web app can access resources from another origin." },
  { term: "Argon2id", category: "Crypto", definition: "The winner of the Password Hashing Competition; a modern memory-hard algorithm resistant to GPU/ASIC brute-forcing." },
  { term: "bcrypt", category: "Crypto", definition: "An adaptive key derivation function based on the Blowfish cipher, widely used for secure password hashing with adjustable work factor." },
  { term: "Salt", category: "Crypto", definition: "Cryptographically random data appended to passwords before hashing to defeat precomputed Rainbow Table attacks." },
  { term: "JWT (JSON Web Token)", category: "Protocols", definition: "A compact, URL-safe standard (RFC 7519) for transmitting claims securely as a signed JSON payload." },
  { term: "WAF (Web Application Firewall)", category: "Defense", definition: "A security filter inspecting incoming HTTP traffic to block SQLi, XSS, and automated malicious bots." },
  { term: "Rate Limiting", category: "Defense", definition: "Restricting the number of requests a client can make in a given timeframe (e.g. 5 attempts/minute) to stop brute-forcing." },
  { term: "CVE (Common Vulnerabilities & Exposures)", category: "Fundamentals", definition: "A standardized dictionary of publicly known cybersecurity vulnerabilities and exposures maintained by MITRE." },
  { term: "CVSS (Common Vulnerability Scoring System)", category: "Fundamentals", definition: "An industry standard (scale 0.0 to 10.0) measuring the severity of security vulnerabilities." },
];

/* ------------------------------------------------------------------ */
/* Interactive Module Card Component                                  */
/* ------------------------------------------------------------------ */

function ModuleCard({
  module,
  isOpen,
  onToggle,
}: {
  module: Module;
  isOpen: boolean;
  onToggle: () => void;
}) {
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
          <span className="flex flex-wrap items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-subtle">
            <span className={accentText(module.accent)}>Module {module.number}</span>
            <span aria-hidden>·</span>
            <span>{module.domain}</span>
            <span aria-hidden>·</span>
            <span className="text-cyan">{module.owaspRef.split(" - ")[0]}</span>
          </span>
          <span className="mt-0.5 block text-lg font-semibold text-foreground">{module.title}</span>
        </span>
        <span className="hidden items-center gap-1.5 font-mono text-[11px] text-subtle sm:flex">
          <Icon name="clock" size={13} /> {module.readMinutes} min read
        </span>
        <Icon
          name="chevron-down"
          size={20}
          className={cx("shrink-0 text-subtle transition-transform duration-300", isOpen && "rotate-180")}
        />
      </button>

      {isOpen && (
        <div id={panelId} className="animate-fade-slide border-t border-border/70 p-6">
          <p className="text-[15px] leading-relaxed text-muted-foreground">{module.intro}</p>

          {/* Real-World Case Study */}
          <div className="mt-6 rounded-xl border border-warning/30 bg-warning/5 p-4 sm:p-5">
            <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-widest text-warning">
              <Icon name="alert-triangle" size={15} /> Real-World Case Study: {module.realWorldBreach.target} ({module.realWorldBreach.year})
            </div>
            <p className="mt-2 text-sm text-foreground/90"><strong>Impact:</strong> {module.realWorldBreach.impact}</p>
            <p className="mt-1 text-sm text-muted-foreground"><strong>Defender Lesson:</strong> {module.realWorldBreach.lesson}</p>
          </div>

          {/* Detailed Sections with Code Snippets */}
          <div className="mt-6 space-y-6">
            {module.sections.map((s) => (
              <div key={s.heading}>
                <h4 className={cx("font-mono text-xs font-semibold uppercase tracking-widest", accentText(module.accent))}>
                  {s.heading}
                </h4>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
                {s.codeSnippet && (
                  <pre className="mt-3 overflow-x-auto rounded-xl border border-border bg-[#080d1a] p-4 font-mono text-xs text-foreground/90 leading-relaxed">
                    <code>{s.codeSnippet}</code>
                  </pre>
                )}
              </div>
            ))}
          </div>

          {/* Defender Implementation Checklist */}
          <div className="mt-8 rounded-xl border border-success/30 bg-success/5 p-5">
            <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-widest text-success">
              <Icon name="check-circle" size={15} /> Defender Implementation Checklist
            </div>
            <ul className="mt-3 space-y-2">
              {module.defenseChecklist.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-foreground/85">
                  <Icon name="check" size={15} className="mt-0.5 shrink-0 text-success" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Key Terms */}
          <div className="mt-6">
            <div className="font-mono text-[10px] uppercase tracking-widest text-subtle">Key Technical Concepts</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {module.keyTerms.map((t) => (
                <Chip key={t}>{t}</Chip>
              ))}
            </div>
          </div>

          {/* Lab Link Button */}
          <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-border/50 pt-5">
            <span className="font-mono text-xs text-muted-foreground">
              Reference: <strong className="text-foreground">{module.owaspRef}</strong> ({module.cweRef})
            </span>
            <PremiumButton
              size="sm"
              variant="outline"
              iconRight="arrow-right"
              onClick={() => navigate({ name: "lab", labId: module.labId })}
            >
              Practise in Lab {module.number}
            </PremiumButton>
          </div>
        </div>
      )}
    </GlowCard>
  );
}

/* ------------------------------------------------------------------ */
/* Main Resources Page Component                                      */
/* ------------------------------------------------------------------ */

export function Resources() {
  const [openId, setOpenId] = useState<string | null>(MODULES[0]?.labId ?? null);
  const [selectedCheatSheet, setSelectedCheatSheet] = useState<string>("headers");
  const [glossaryFilter, setGlossaryFilter] = useState<string>("All");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const filteredGlossary = useMemo(() => {
    return GLOSSARY.filter((item) => {
      const matchesCategory = glossaryFilter === "All" || item.category === glossaryFilter;
      const matchesSearch =
        searchTerm === "" ||
        item.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.definition.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }, [glossaryFilter, searchTerm]);

  const activeCheatSheet = useMemo(() => {
    return CHEAT_SHEETS.find((c) => c.id === selectedCheatSheet) || CHEAT_SHEETS[0];
  }, [selectedCheatSheet]);

  return (
    <div className="mx-auto max-w-5xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <SectionHeader
        eyebrow="Resources & Study Library"
        title="Cybersecurity Knowledge Base"
        description="Comprehensive learning curriculum, attack breakdowns, code mitigation blueprints, and cheat sheets for student defenders."
      />

      {/* 1. Foundations Primer */}
      <Reveal className="mt-14">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
          <Icon name="compass" size={14} /> Core Security Foundations
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FOUNDATIONS.map((f) => (
            <div key={f.title} className="flex flex-col justify-between rounded-2xl border border-border bg-card p-5 transition-all duration-300 hover:border-cyan/40">
              <div>
                <div className={cx("flex items-center gap-2", accentText(f.accent))}>
                  <Icon name={f.icon} size={18} />
                  <h3 className="text-base font-semibold text-foreground">{f.title}</h3>
                </div>
                <div className="mt-1 font-mono text-[11px] text-cyan/80">{f.subtitle}</div>
                <p className="mt-2.5 text-xs leading-relaxed text-muted-foreground">{f.body}</p>
              </div>
            </div>
          ))}
        </div>
      </Reveal>

      {/* 2. Deep-Dive Study Modules */}
      <Reveal className="mt-14">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
            <Icon name="book" size={14} /> Interactive Study Modules & Labs
          </div>
          <span className="font-mono text-xs text-muted-foreground hidden sm:inline">5 In-Depth Domains</span>
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

      {/* 3. Quick Reference Cheat Sheets */}
      <Reveal className="mt-16">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
          <Icon name="terminal" size={14} /> Defender's Cheat Sheets & Standards
        </div>
        <div className="mt-4 rounded-2xl border border-border bg-card p-6">
          {/* Tab Selector */}
          <div className="flex flex-wrap gap-2 border-b border-border/70 pb-4">
            {CHEAT_SHEETS.map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedCheatSheet(c.id)}
                className={cx(
                  "flex items-center gap-2 rounded-xl px-4 py-2 font-mono text-xs transition-all",
                  selectedCheatSheet === c.id
                    ? "bg-cyan/15 text-cyan border border-cyan/40 font-semibold"
                    : "text-muted-foreground hover:bg-surface hover:text-foreground"
                )}
              >
                <Icon name={c.icon} size={14} />
                {c.title}
              </button>
            ))}
          </div>

          {/* Active Cheat Sheet Grid */}
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {activeCheatSheet.items.map((item) => (
              <div key={item.key} className="rounded-xl border border-border/80 bg-surface/60 p-4">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-mono text-xs font-semibold text-foreground">{item.key}</span>
                  {item.badge && (
                    <span
                      className={cx(
                        "rounded px-2 py-0.5 font-mono text-[10px] font-semibold uppercase",
                        item.badgeType === "good"
                          ? "bg-success/15 text-success"
                          : item.badgeType === "warn"
                          ? "bg-warning/15 text-warning"
                          : "bg-cyan/15 text-cyan"
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
                <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{item.desc}</p>
                {item.recommendedValue && (
                  <div className="mt-3 overflow-x-auto rounded-lg bg-[#060a14] p-2.5 font-mono text-[11px] text-cyan border border-cyan/20">
                    <code>{item.recommendedValue}</code>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </Reveal>

      {/* 4. External Free Learning Platforms & Tools */}
      <Reveal className="mt-16">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
          <Icon name="link" size={14} /> Industry Tools & Free Practice Portals
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {EXTERNAL_RESOURCES.map((r) => (
            <a
              key={r.title}
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col justify-between rounded-2xl border border-border bg-card p-5 transition-all duration-300 hover:-translate-y-1 hover:border-cyan/50 hover:shadow-lg hover:shadow-cyan/5"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="grid h-9 w-9 place-items-center rounded-lg bg-cyan/10 text-cyan">
                    <Icon name={r.icon} size={18} />
                  </span>
                  <Icon name="arrow-up-right" size={16} className="text-subtle transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-cyan" />
                </div>
                <span className="mt-3 block font-mono text-[10px] uppercase tracking-widest text-cyan">{r.category}</span>
                <h4 className="mt-1 text-sm font-semibold text-foreground group-hover:text-cyan transition-colors">{r.title}</h4>
                <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{r.desc}</p>
              </div>
              <div className="mt-4 flex items-center gap-1 font-mono text-[11px] text-subtle group-hover:text-foreground">
                <span>Visit Resource</span>
                <Icon name="chevron-right" size={12} />
              </div>
            </a>
          ))}
        </div>
      </Reveal>

      {/* 5. Searchable Cyber Glossary (30+ Terms) */}
      <Reveal className="mt-16">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-cyan">
            <Icon name="search" size={14} /> Searchable Cybersecurity Glossary ({GLOSSARY.length} Terms)
          </div>

          {/* Category Filter Chips */}
          <div className="flex flex-wrap gap-1.5">
            {["All", "Fundamentals", "Attacks", "Defense", "Protocols", "Crypto"].map((cat) => (
              <button
                key={cat}
                onClick={() => setGlossaryFilter(cat)}
                className={cx(
                  "rounded-lg px-2.5 py-1 font-mono text-[11px] transition-all",
                  glossaryFilter === cat
                    ? "bg-cyan text-[#060a14] font-semibold"
                    : "bg-surface text-muted-foreground hover:text-foreground border border-border"
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Search Input Bar */}
        <div className="mt-4 relative">
          <Icon name="search" size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-subtle" />
          <input
            type="text"
            placeholder="Search cybersecurity terminology (e.g. XSS, IDOR, CSP, HSTS, Salt, Salt, JWT)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-border bg-card py-2.5 pl-10 pr-4 font-mono text-xs text-foreground placeholder:text-subtle focus:border-cyan focus:outline-none focus:ring-1 focus:ring-cyan"
          />
        </div>

        {/* Glossary Grid */}
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {filteredGlossary.map((g) => (
            <div key={g.term} className="rounded-xl border border-border bg-card p-4 transition-colors hover:border-border/80">
              <div className="flex items-center justify-between">
                <dt className="text-sm font-semibold text-foreground">{g.term}</dt>
                <span className="rounded bg-surface px-2 py-0.5 font-mono text-[10px] uppercase text-cyan border border-border">
                  {g.category}
                </span>
              </div>
              <dd className="mt-2 text-xs leading-relaxed text-muted-foreground">{g.definition}</dd>
            </div>
          ))}
          {filteredGlossary.length === 0 && (
            <div className="col-span-full rounded-xl border border-dashed border-border p-8 text-center">
              <p className="text-sm text-muted-foreground">No matching cybersecurity terms found for "{searchTerm}".</p>
            </div>
          )}
        </div>
      </Reveal>
    </div>
  );
}
