import type { Lab } from "./types";

export const LABS: Lab[] = [
  {
    id: "auth",
    number: 1,
    title: "The Weak Front Door",
    codename: "Authentication",
    slug: "authentication",
    prerequisiteLabs: [],
    security: {
      asset: "User accounts and the list of who has one.",
      threat: "An attacker maps valid usernames, then targets brute-force / credential-stuffing at accounts they know exist.",
      weakness: "Login responses differ for real vs. non-existent users (username enumeration).",
      learningGoal: "Recognise how error-message and response differences leak account existence.",
      safeBoundary: "A fixed, in-memory portal with two scripted responses — no real authentication service, network calls, or accounts.",
      successCondition: "Correctly identify user enumeration as the core weakness.",
      remediation: "Return one generic failure message, rate-limit login attempts, and require multi-factor authentication.",
    },
    category: "Identity",
    difficulty: "Beginner",
    estMinutes: 15,
    accent: "cyan",
    skills: ["Credential handling", "Brute-force awareness", "Session basics"],
    summary:
      "Investigate a login portal that trusts too much. Learn how attackers exploit weak authentication before a single password is guessed.",
    mission:
      "The employee portal for Northstar Systems keeps getting compromised. Examine the login flow and identify the flaw that lets attackers walk right in.",
    objectives: [
      "Observe the login response behaviour",
      "Compare messages for valid vs invalid users",
      "Identify the authentication weakness",
    ],
    simulation: "browser",
    sim: {
      url: "https://portal.northstar-systems.internal/login",
      title: "Northstar Employee Portal",
      responses: [
        { user: "j.doe", exists: true, message: "Wrong password for j.doe." },
        { user: "ghost99", exists: false, message: "No account found for ghost99." },
      ],
    },
    hints: [
      "Try two different usernames — one real, one fake. Read each message carefully.",
      "The portal tells you *whether the account exists* before any password check.",
      "This is called username enumeration — it hands attackers a valid user list for free.",
    ],
    steps: [
      {
        id: "observe-valid",
        kind: "observe",
        title: "Observe a known account",
        prompt:
          "Sign in as the real employee `j.doe` with any password. Read exactly what the server says back.",
        requires: ["login:valid"],
        explanation:
          "For a real account, the portal reports a password problem — confirming the account exists.",
      },
      {
        id: "probe-invalid",
        kind: "probe",
        title: "Probe a non-existent account",
        prompt:
          "Now try `ghost99`, a username that doesn't exist. Compare its response to the previous one.",
        requires: ["login:invalid"],
        explanation:
          "For a fake account, the portal says *no account found* — a different message entirely.",
      },
      {
        id: "decide-weakness",
        kind: "decide",
        title: "Name the trust boundary that leaks",
        prompt: "The two responses differ. What is the login flow incorrectly revealing?",
        question: "What is the core authentication weakness in this portal?",
        options: [
          { id: "a", label: "Passwords are stored in plaintext" },
          { id: "b", label: "The login form lacks HTTPS" },
          {
            id: "c",
            label: "Error messages reveal whether a username exists (user enumeration)",
          },
          { id: "d", label: "Sessions never expire" },
        ],
        answer: "c",
        wrongFeedback:
          "Look again at the two responses — the difference between them is the clue. The portal behaves differently for real vs fake accounts.",
        explanation:
          "Distinct messages for real vs fake usernames let an attacker enumerate a valid account list before guessing a single password.",
      },
      {
        id: "decide-control",
        kind: "decide",
        title: "Choose the defensive control",
        prompt: "You've found the weakness. Which control most directly closes it?",
        question: "Which defensive change best fixes this weakness?",
        options: [
          { id: "a", label: "Force a password change every 30 days" },
          {
            id: "b",
            label: "Return one generic 'Invalid credentials' message for every failed login",
          },
          { id: "c", label: "Hide the login form behind a CAPTCHA only" },
          { id: "d", label: "Log failed attempts to a file" },
        ],
        answer: "b",
        wrongFeedback:
          "The leak comes from *different* messages. Rotation, CAPTCHA and logging help elsewhere but don't stop enumeration.",
        explanation:
          "One identical failure message removes the signal. Pair it with rate limiting and MFA for defence in depth.",
      },
    ],
    question: "What is the core authentication weakness in this portal?",
    options: [
      { id: "a", label: "Passwords are stored in plaintext" },
      { id: "b", label: "The login form lacks HTTPS" },
      {
        id: "c",
        label: "Error messages reveal whether a username exists (user enumeration)",
      },
      { id: "d", label: "Sessions never expire" },
    ],
    answer: "c",
    wrongFeedback:
      "Look again at the two responses — the difference between them is the clue. The portal behaves differently for real vs fake accounts.",
    baseScore: 100,
    outcome: {
      discovered:
        "The portal returns distinct messages for existing and non-existing usernames, leaking a valid account list.",
      whyItMatters:
        "Username enumeration turns a blind brute-force into a targeted one. Attackers focus only on accounts they know exist, dramatically improving success rates.",
      secureApproach:
        "Return a single generic message ('Invalid credentials') for every failed login, apply rate limiting, and add multi-factor authentication.",
      nextSkill: "Once identity is verified, the next question is what a user is *allowed* to do.",
    },
  },
  {
    id: "authz",
    number: 2,
    title: "Who Owns This Record?",
    codename: "Authorization",
    slug: "authorization",
    prerequisiteLabs: ["auth"],
    security: {
      asset: "Customer support records belonging to other account holders.",
      threat: "An authenticated attacker reads or edits objects they do not own by tampering with an identifier.",
      weakness: "The server verifies identity but never checks object ownership (IDOR).",
      learningGoal: "Distinguish authentication (who you are) from authorization (what you may access).",
      safeBoundary: "Four fictional records held in memory; changing the id only reveals scripted sample data — no database or real customers.",
      successCondition: "Correctly identify the missing ownership check (IDOR).",
      remediation: "Authorize every object access server-side against the current user before returning it.",
    },
    category: "Access Control",
    difficulty: "Beginner",
    estMinutes: 20,
    accent: "primary",
    skills: ["IDOR", "Access control", "Object ownership"],
    summary:
      "A customer support console checks who you are — but never checks what is yours. Discover Insecure Direct Object Reference (IDOR).",
    mission:
      "You are signed in to the Northstar Customer Support console as account #1001. Explore the record viewer and its request inspector to determine whether you can reach data that isn't yours.",
    objectives: [
      "Open your own record (#1001)",
      "Request another customer's record via its identifier",
      "Read the simulated request and decide whether ownership is enforced",
    ],
    simulation: "browser",
    sim: {
      url: "https://support.northstar-systems.example/records?id=1001",
      title: "Northstar Customer Support",
      you: "1001",
      records: {
        "1001": { name: "You (M. Rao)", note: "Billing question — resolved. Plan: Standard." },
        "1002": { name: "A. Fernandez", note: "Refund dispute — card ending 4417. Confidential." },
        "1003": { name: "K. Whitmore", note: "Account recovery — security answers on file." },
        "1004": { name: "D. Osei", note: "Enterprise contract — pricing NDA. Confidential." },
      },
    },
    hints: [
      "Your record is #1001. What happens if you request #1002 instead?",
      "The server checks that you're logged in — but does it check the record belongs to you?",
      "Reading another customer's record by changing an ID is a classic IDOR flaw.",
    ],
    steps: [
      {
        id: "observe-own",
        kind: "observe",
        title: "Open your own record",
        prompt: "Load record #1001 — your own account. Note that the request succeeds because you're authenticated.",
        requires: ["view:1001"],
        explanation: "Authentication works: the server knows who you are and returns your record.",
      },
      {
        id: "probe-other",
        kind: "probe",
        title: "Request a record that isn't yours",
        prompt:
          "Change the id in the address bar to another customer (1002, 1003 or 1004) and watch the simulated request `GET /simulated-record/100x`.",
        requires: ["view:other"],
        explanation:
          "The same authenticated session returns a stranger's record. Knowing the identifier was enough — no ownership was checked.",
      },
      {
        id: "decide-flaw",
        kind: "decide",
        title: "Explain the exposure",
        prompt: "You just read a record you don't own. Why was that possible?",
        question: "Why can you read customer #1002's record?",
        options: [
          { id: "a", label: "The record IDs are encrypted, so guessing worked by luck" },
          {
            id: "b",
            label: "The server authenticates you but never authorises object ownership (IDOR)",
          },
          { id: "c", label: "The database has no passwords" },
          { id: "d", label: "The browser cached another user's page" },
        ],
        answer: "b",
        wrongFeedback:
          "You were logged in the whole time, so authentication worked. The gap is that nothing verified the record actually belongs to you.",
        explanation:
          "Knowing an identifier is not the same as having permission. The server trusted the id in the request without an ownership check.",
      },
      {
        id: "decide-fix",
        kind: "decide",
        title: "Choose the remediation",
        prompt: "Where must the fix live to reliably stop this?",
        question: "What is the correct remediation for object-level authorization failure?",
        options: [
          { id: "a", label: "Obfuscate or randomise the record IDs so they're hard to guess" },
          { id: "b", label: "Hide the id from the URL and send it in a header instead" },
          {
            id: "c",
            label: "Check server-side that the current user owns (or may access) the object before returning it",
          },
          { id: "d", label: "Rate-limit how many records a session can request per minute" },
        ],
        answer: "c",
        wrongFeedback:
          "Obfuscation and header tricks are security-by-obscurity — the id is still guessable. The check must be an explicit server-side ownership decision.",
        explanation:
          "Authorize every object access against the authenticated user, server-side, on every request. Unguessable IDs are not a substitute.",
      },
    ],
    question: "Why can you read customer #1002's record?",
    options: [
      { id: "a", label: "The record IDs are encrypted, so guessing worked by luck" },
      {
        id: "b",
        label: "The server authenticates you but never authorises object ownership (IDOR)",
      },
      { id: "c", label: "The database has no passwords" },
      { id: "d", label: "The browser cached another user's page" },
    ],
    answer: "b",
    wrongFeedback:
      "You were logged in the whole time, so authentication worked. The gap is that nothing verified the record actually belongs to you.",
    baseScore: 120,
    outcome: {
      discovered:
        "Changing the record ID in the request exposed other customers' confidential data. The app authenticated you but never authorised the request.",
      whyItMatters:
        "IDOR is one of the most common and damaging web flaws. A single predictable ID can leak an entire database of private records.",
      secureApproach:
        "Enforce ownership on every request server-side: verify the authenticated user actually owns (or is permitted to access) the requested object before returning it.",
      nextSkill: "Access control assumes clean input. Next, learn what happens when input turns hostile.",
    },
  },
  {
    id: "input",
    number: 3,
    title: "Trust No Input",
    codename: "Input Validation",
    slug: "input-validation",
    prerequisiteLabs: ["authz"],
    security: {
      asset: "The integrity of the rendered page and every visitor's browser session.",
      threat: "An attacker injects markup/script that runs in other users' browsers (Cross-Site Scripting).",
      weakness: "User input is reflected into the page as HTML instead of being escaped as text.",
      learningGoal: "See why untrusted input must be treated as data, never as executable markup.",
      safeBoundary: "The demo renders your input only inside this isolated lab widget; no payload leaves the page or reaches another user.",
      successCondition: "Correctly identify reflected XSS via unescaped output.",
      remediation: "Context-encode all output, validate input against an allow-list, and enforce a strict Content-Security-Policy.",
    },
    category: "Injection",
    difficulty: "Intermediate",
    estMinutes: 25,
    accent: "violet",
    skills: ["XSS", "Output encoding", "Sanitisation"],
    summary:
      "The Atlas Feedback Portal accepts whatever you send it. Run a battery of predefined test inputs and learn which ones the app should have rejected — and why one becomes Cross-Site Scripting.",
    mission:
      "Use the test-input toolbox to probe the Atlas Feedback Portal. Each test is predefined and safe — no input is executed as code except the contained demo. Record what the app accepts and identify the missing controls.",
    objectives: [
      "Run the baseline 'normal input' test",
      "Run the 'unexpected characters' test and watch how it is rendered",
      "Complete the full test matrix and identify the vulnerability + fix",
    ],
    simulation: "form",
    sim: {
      app: "Atlas Feedback Portal",
      note: "SAFE EDUCATIONAL SIMULATION — every test input below is predefined. Nothing you type is executed.",
      tests: [
        {
          id: "normal",
          label: "Normal input",
          field: "Feedback",
          input: "Great portal, thanks for the quick help!",
          result: "accepted",
          observation: "Stored and displayed as plain text.",
          impact: "None — this is expected, well-formed input.",
          severity: "ok",
        },
        {
          id: "empty",
          label: "Empty submission",
          field: "Feedback",
          input: "",
          result: "accepted",
          observation: "A blank feedback record is saved with no error.",
          impact: "Missing required-field validation — junk records accumulate.",
          severity: "low",
        },
        {
          id: "email",
          label: "Malformed email",
          field: "Email",
          input: "rao(at)atlas",
          result: "accepted",
          observation: "An address with no @ or domain is accepted.",
          impact: "Broken follow-up, bounced mail, unverifiable identity.",
          severity: "low",
        },
        {
          id: "length",
          label: "Excessive length",
          field: "Feedback",
          input: "A… (5,000 characters)",
          result: "accepted",
          observation: "A 5,000-character body is stored untrimmed.",
          impact: "Storage abuse and possible denial-of-service — no length bound.",
          severity: "medium",
        },
        {
          id: "chars",
          label: "Unexpected characters (markup)",
          field: "Feedback",
          input: "<img src=x onerror=alert('xss')>",
          result: "reflected",
          observation: "The markup is rendered as live HTML instead of shown as text.",
          impact: "Reflected XSS — attacker-supplied script runs in a visitor's browser.",
          severity: "high",
          reflect: true,
        },
        {
          id: "boundary",
          label: "Boundary value",
          field: "Category",
          input: "0 / -1 / 999999999",
          result: "accepted",
          observation: "Out-of-range category ids are accepted without a check.",
          impact: "Logic errors — feedback references categories that don't exist.",
          severity: "medium",
        },
        {
          id: "type",
          label: "Unexpected type",
          field: "Rating",
          input: '{"rating": true}',
          result: "accepted",
          observation: "A JSON object is accepted where a number was expected.",
          impact: "Type confusion downstream — parser and math assumptions break.",
          severity: "medium",
        },
      ],
    },
    hints: [
      "Start with 'Normal input' to see the baseline, then try 'Unexpected characters'.",
      "Watch the markup test closely — if tags render as real HTML instead of text, output isn't being escaped.",
      "Reflected, unescaped input that the browser executes is Cross-Site Scripting (XSS).",
    ],
    steps: [
      {
        id: "observe-normal",
        kind: "observe",
        title: "Establish a baseline",
        prompt: "Run the 'Normal input' test. Confirm well-formed feedback is stored and shown as plain text.",
        requires: ["test:normal"],
        explanation: "Expected input behaves correctly — that's your baseline for comparison.",
      },
      {
        id: "probe-chars",
        kind: "probe",
        title: "Send unexpected characters",
        prompt: "Run the 'Unexpected characters (markup)' test and watch how the portal renders it.",
        requires: ["test:chars"],
        explanation: "The predefined markup renders as live HTML — the app treated untrusted input as code, not data.",
      },
      {
        id: "probe-matrix",
        kind: "probe",
        title: "Complete the test matrix",
        prompt: "Run the remaining tests so every row of the results table is filled in.",
        requires: ["tests:complete"],
        explanation: "The matrix shows a pattern: the portal accepts almost anything and validates almost nothing.",
      },
      {
        id: "decide-vuln",
        kind: "decide",
        title: "Identify the vulnerability",
        prompt: "One test result is a genuine security vulnerability, not just sloppy validation. Which class is it?",
        question: "What vulnerability does the unescaped markup demonstrate?",
        options: [
          { id: "a", label: "SQL Injection" },
          { id: "b", label: "Cross-Site Scripting (XSS) via unescaped output" },
          { id: "c", label: "Cross-Site Request Forgery (CSRF)" },
          { id: "d", label: "Clickjacking" },
        ],
        answer: "b",
        wrongFeedback:
          "The flaw is markup being rendered as code in the page, not database queries or forged requests. Look at how the markup test was displayed.",
        explanation:
          "Reflecting untrusted input as HTML lets the browser execute it — that is reflected XSS.",
      },
      {
        id: "decide-control",
        kind: "decide",
        title: "Choose the control set",
        prompt: "Which combination best defends against this class of flaw?",
        question: "Which controls together prevent this input-handling failure?",
        options: [
          { id: "a", label: "A longer password policy and account lockout" },
          {
            id: "b",
            label: "Context-aware output encoding, allow-list input validation, and a strict Content-Security-Policy",
          },
          { id: "c", label: "HTTPS on the login page only" },
          { id: "d", label: "Disabling JavaScript for all users" },
        ],
        answer: "b",
        wrongFeedback:
          "Passwords and login TLS don't touch how this output is rendered. The fix is about treating input as data and encoding output.",
        explanation:
          "Encode on output for the right context, validate input against an allow-list, and add CSP as defence in depth.",
      },
    ],
    question: "What vulnerability does this comment box demonstrate?",
    options: [
      { id: "a", label: "SQL Injection" },
      { id: "b", label: "Cross-Site Scripting (XSS) via unescaped output" },
      { id: "c", label: "Cross-Site Request Forgery (CSRF)" },
      { id: "d", label: "Clickjacking" },
    ],
    answer: "b",
    wrongFeedback:
      "The flaw is about markup being rendered as code in the page, not about database queries or forged requests. Look at how your HTML was displayed.",
    baseScore: 150,
    outcome: {
      discovered:
        "The comment box rendered your HTML markup as live code instead of plain text — the browser executed injected script.",
      whyItMatters:
        "XSS lets attackers run code in victims' browsers: stealing sessions, keylogging, or defacing pages. Stored XSS can hit every visitor to a page.",
      secureApproach:
        "Contextually encode all output, validate input against an allow-list, and apply a strict Content-Security-Policy as defence in depth.",
      nextSkill: "Even clean code fails if the platform around it is misconfigured. Next: security configuration.",
    },
  },
  {
    id: "config",
    number: 4,
    title: "The Unlocked Server",
    codename: "Security Configuration",
    slug: "security-configuration",
    prerequisiteLabs: ["input"],
    security: {
      asset: "The production application and its administrative access.",
      threat: "An attacker exploits insecure defaults — default credentials, debug mode, wildcard CORS — for an easy foothold.",
      weakness: "Factory/development settings shipped to a production deployment.",
      learningGoal: "Learn to audit configuration and rank misconfigurations by real impact.",
      safeBoundary: "A static, fictional config manifest rendered in the lab; nothing is deployed, connected, or executed.",
      successCondition: "Correctly select the default admin password as the most critical issue.",
      remediation: "Harden by default: rotate every credential, disable debug in production, scope CORS, and audit config in CI.",
    },
    category: "Hardening",
    difficulty: "Intermediate",
    estMinutes: 25,
    accent: "warning",
    skills: ["Hardening", "Secrets exposure", "Defaults"],
    summary:
      "The Northstar Operations Dashboard is about to ship with factory settings. Audit the production configuration by section, rank findings by real impact, and compare against a hardened baseline.",
    mission:
      "Review the production configuration for the Northstar Operations Dashboard. Flag the insecure settings, rank them by impact, and confirm the hardened values. This is a static, fictional config — nothing is deployed or connected.",
    objectives: [
      "Review every configuration section",
      "Flag the insecure settings by severity",
      "Rank the most dangerous finding and confirm the hardened baseline",
    ],
    simulation: "config",
    sim: {
      filename: "northstar-ops.production.env",
      lines: [
        {
          key: "NODE_ENV",
          value: "development",
          section: "Application",
          severity: "medium",
          reason: "Production runs with development safeguards disabled.",
          secure: "production",
        },
        {
          key: "DEBUG",
          value: "true",
          section: "Debugging",
          severity: "high",
          reason: "Verbose debug output and stack traces returned to users.",
          secure: "false",
        },
        {
          key: "LOG_PII",
          value: "true",
          section: "Logging",
          severity: "medium",
          reason: "Personal data written to plain application logs.",
          secure: "false",
        },
        {
          key: "SHOW_STACK_TRACES",
          value: "true",
          section: "Error Handling",
          severity: "medium",
          reason: "Internal paths, versions and queries leak on every error.",
          secure: "false",
        },
        {
          key: "SESSION_SECRET",
          value: "changeme",
          section: "Sessions",
          severity: "high",
          reason: "Default signing secret — session tokens can be forged.",
          secure: "<64-char random secret>",
        },
        {
          key: "COOKIE_SECURE",
          value: "false",
          section: "Sessions",
          severity: "high",
          reason: "Session cookie is sent over plaintext connections.",
          secure: "true",
        },
        {
          key: "ADMIN_PASSWORD",
          value: "admin",
          section: "Security",
          severity: "high",
          reason: "Default admin credential — instant, effortless full control.",
          secure: "<rotated strong secret>",
        },
        {
          key: "CORS_ORIGIN",
          value: "*",
          section: "Security",
          severity: "medium",
          reason: "Any website can call the API from a victim's browser.",
          secure: "https://app.northstar-systems.example",
        },
        {
          key: "TLS",
          value: "enabled",
          section: "Security",
          severity: "ok",
          reason: "Transport encryption is on — this line is correct.",
          secure: "enabled",
        },
      ],
    },
    hints: [
      "Work section by section. Not every issue is equally severe — reserve High for the worst.",
      "Debug output and stack traces leak internals, but one line hands an attacker the keys directly.",
      "A default admin password ('admin') is game over — it's the single most dangerous line here.",
    ],
    steps: [
      {
        id: "observe-review",
        kind: "observe",
        title: "Review the configuration",
        prompt: "Read through every section of the production config. Note which lines look like untouched defaults.",
        explanation: "Six sections, one hardened line (TLS). Everything else deserves scrutiny.",
      },
      {
        id: "probe-flag",
        kind: "probe",
        title: "Flag the insecure settings",
        prompt: "Flag at least three settings that should never ship to production.",
        requires: ["flag:3"],
        explanation: "Flagging forces you to justify each finding — reason and severity, not a blanket 'Critical'.",
      },
      {
        id: "decide-critical",
        kind: "decide",
        title: "Rank by impact",
        prompt: "All of these are real problems. Which single line gives an attacker instant full control with zero effort?",
        question: "Which misconfiguration is the most dangerous to fix first?",
        options: [
          { id: "a", label: "NODE_ENV set to development" },
          { id: "b", label: "CORS_ORIGIN set to '*'" },
          { id: "c", label: "ADMIN_PASSWORD left as the default 'admin'" },
          { id: "d", label: "DEBUG enabled" },
        ],
        answer: "c",
        wrongFeedback:
          "Those are all real problems — but rank by impact. Which one gives an attacker instant full control with zero effort?",
        explanation:
          "A default admin credential is immediate, complete compromise. Debug/CORS/env issues widen exposure but don't hand over the keys directly.",
      },
      {
        id: "observe-diff",
        kind: "observe",
        title: "Compare against the hardened baseline",
        prompt: "Toggle the secure baseline to see the before/after for each setting.",
        requires: ["diff:viewed"],
        explanation: "A hardened baseline turns ad-hoc review into a repeatable, auditable standard.",
      },
      {
        id: "decide-principle",
        kind: "decide",
        title: "Name the governing principle",
        prompt: "What practice would have prevented this entire class of finding?",
        question: "Which principle best prevents security misconfiguration?",
        options: [
          { id: "a", label: "Manually double-checking config right before each release" },
          {
            id: "b",
            label: "Secure defaults plus automated configuration checks enforced in CI",
          },
          { id: "c", label: "Giving only senior engineers access to the config file" },
          { id: "d", label: "Encrypting the .env file at rest" },
        ],
        answer: "b",
        wrongFeedback:
          "Manual checks and access limits help but rely on humans remembering. The durable fix is safe defaults verified automatically.",
        explanation:
          "Harden by default and fail the build when insecure values appear — misconfiguration then can't reach production.",
      },
    ],
    question: "Which misconfiguration is the most critical to fix first?",
    options: [
      { id: "a", label: "NODE_ENV set to development" },
      { id: "b", label: "CORS_ORIGIN set to '*'" },
      { id: "c", label: "ADMIN_PASSWORD left as the default 'admin'" },
      { id: "d", label: "DEBUG enabled" },
    ],
    answer: "c",
    wrongFeedback:
      "Those are all real problems — but rank by impact. Which one gives an attacker instant full control with zero effort?",
    baseScore: 150,
    outcome: {
      discovered:
        "The production config shipped with a default admin password, debug mode on, and a wildcard CORS policy.",
      whyItMatters:
        "Security misconfiguration is consistently among the most exploited categories. Default credentials and verbose errors give attackers a foothold before any real exploit is needed.",
      secureApproach:
        "Harden by default: rotate every credential, disable debug in production, scope CORS to known origins, and automate config audits in CI.",
      nextSkill: "Configuration lives in the traffic itself. Final lab: read the raw HTTP conversation.",
    },
  },
  {
    id: "http",
    number: 5,
    title: "Reading the Wire",
    codename: "HTTP Security Analysis",
    slug: "http-security-analysis",
    prerequisiteLabs: ["config"],
    security: {
      asset: "The user's session and the confidentiality of data in transit.",
      threat: "An attacker steals or replays a session cookie to take over the account (session hijacking).",
      weakness: "Session cookie issued without Secure, HttpOnly, and SameSite; missing security headers (HSTS, X-Content-Type-Options).",
      learningGoal: "Read a raw HTTP exchange and reason about headers and cookie flags as a security surface.",
      safeBoundary: "A single captured, fictional request/response pair shown as static text — no live traffic, host, or bank is contacted.",
      successCondition: "Correctly identify the missing session-cookie attributes as the most serious issue.",
      remediation: "Set cookies with Secure; HttpOnly; SameSite=Strict, enforce HSTS, and add X-Content-Type-Options: nosniff.",
    },
    category: "Traffic Analysis",
    difficulty: "Advanced",
    estMinutes: 30,
    accent: "success",
    skills: ["HTTP headers", "Cookies", "Traffic analysis"],
    summary:
      "Every secret a web app keeps eventually crosses the wire. Inspect a captured request/response pair from Atlas Notes line by line, then combine everything you've learned to judge its security.",
    mission:
      "Analyse this captured HTTP exchange from the Atlas Notes API. Read the request and response in the inspector, work through five focused questions, then deliver a combined assessment. The exchange is a single, fictional, static capture — no live traffic is involved.",
    objectives: [
      "Explore the request and response in the inspector",
      "Identify the method, user-controlled data, and missing headers",
      "Compare the insecure response with a safer one and deliver a final verdict",
    ],
    simulation: "request",
    sim: {
      request: {
        method: "GET",
        path: "/api/notes/482",
        host: "api.atlas-notes.example",
        headers: {
          Host: "api.atlas-notes.example",
          "User-Agent": "Mozilla/5.0",
          Accept: "application/json",
          Cookie: "session=eyJhbGciOi...; theme=dark",
        },
        query: { id: "482", shared: "true" },
      },
      response: {
        status: 200,
        statusText: "OK",
        headers: {
          "Content-Type": "application/json",
          "Set-Cookie": "session=eyJhbGciOi...; Path=/",
          "Cache-Control": "no-store",
          Server: "nginx/1.24.0",
        },
        body: { id: 482, title: "Q3 roadmap", visibility: "private", owner: "m.rao" },
        missing: ["Strict-Transport-Security", "X-Content-Type-Options"],
        cookieIssues: ["Missing Secure", "Missing HttpOnly", "Missing SameSite"],
        safeSetCookie: "session=eyJhbGciOi...; Path=/; Secure; HttpOnly; SameSite=Strict",
        safeHeaders: {
          "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
          "X-Content-Type-Options": "nosniff",
        },
      },
    },
    hints: [
      "Switch between REQUEST and RESPONSE and open every tab before answering.",
      "For the cookie questions, focus on the Set-Cookie header's attributes — what's present and what's missing.",
      "Missing HttpOnly means JavaScript (and any XSS from Lab 03) can read the session cookie directly.",
    ],
    steps: [
      {
        id: "observe-explore",
        kind: "observe",
        title: "Explore the exchange",
        prompt: "Open the inspector and switch between the REQUEST and RESPONSE sides and their tabs.",
        requires: ["viewer:explored"],
        explanation: "You now have the full picture: method, query, headers, cookies and body.",
      },
      {
        id: "decide-method",
        kind: "decide",
        title: "Identify the method",
        prompt: "Which HTTP method does this request use?",
        question: "What HTTP method is used in this request?",
        options: [
          { id: "a", label: "GET" },
          { id: "b", label: "POST" },
          { id: "c", label: "PUT" },
          { id: "d", label: "DELETE" },
        ],
        answer: "a",
        wrongFeedback: "Check the method shown at the top of the request in the inspector.",
        explanation: "A GET request — its parameters ride in the URL query string, which matters for the next question.",
      },
      {
        id: "decide-usercontrolled",
        kind: "decide",
        title: "Spot the user-controlled data",
        prompt: "Which part of this request is directly controlled by the client and must be treated as untrusted?",
        question: "Which part of the request carries user-controlled data?",
        options: [
          { id: "a", label: "The Server response header" },
          { id: "b", label: "The query-string parameters (id, shared)" },
          { id: "c", label: "The Content-Type of the response" },
          { id: "d", label: "The HTTP status code" },
        ],
        answer: "b",
        wrongFeedback: "Response headers and status come from the server. Look at what the client sends in the URL.",
        explanation: "The `id` and `shared` query params are attacker-controllable — exactly the surface Labs 02 and 03 warned about.",
      },
      {
        id: "decide-missing-header",
        kind: "decide",
        title: "Find the missing protection",
        prompt: "One important transport-security header is absent from the response. Which?",
        question: "Which security header is missing from the response?",
        options: [
          { id: "a", label: "Cache-Control" },
          { id: "b", label: "Content-Type" },
          { id: "c", label: "Strict-Transport-Security (HSTS)" },
          { id: "d", label: "Server" },
        ],
        answer: "c",
        wrongFeedback: "Cache-Control, Content-Type and Server are all present. Check the 'Missing security headers' list on the response overview.",
        explanation: "Without HSTS, a browser can be downgraded to plaintext HTTP, exposing the very cookie in this exchange.",
      },
      {
        id: "decide-header-purpose",
        kind: "decide",
        title: "Explain a cookie attribute",
        prompt: "The session cookie is missing HttpOnly. What does adding HttpOnly accomplish?",
        question: "What does the HttpOnly attribute on a session cookie do?",
        options: [
          { id: "a", label: "Encrypts the cookie value at rest" },
          { id: "b", label: "Stops JavaScript from reading the cookie, blunting XSS-based theft" },
          { id: "c", label: "Prevents the cookie from ever expiring" },
          { id: "d", label: "Sends the cookie only to the same site" },
        ],
        answer: "b",
        wrongFeedback: "SameSite handles cross-site sending; HttpOnly is specifically about script access to the cookie.",
        explanation: "HttpOnly keeps `document.cookie` from exposing the session, so an XSS payload can't simply steal it.",
      },
      {
        id: "decide-compare",
        kind: "decide",
        title: "Compare insecure vs safer",
        prompt: "Compare the captured Set-Cookie with the safer version shown. What is the essential fix?",
        question: "What is the key difference that makes the safer response secure?",
        options: [
          { id: "a", label: "It removes the Cache-Control header" },
          { id: "b", label: "It hides the Server version number only" },
          {
            id: "c",
            label: "The session cookie carries Secure; HttpOnly; SameSite and HSTS is added",
          },
          { id: "d", label: "It changes the method from GET to POST" },
        ],
        answer: "c",
        wrongFeedback: "The decisive change is on the session cookie's attributes and the added transport-security header.",
        explanation: "Secure + HttpOnly + SameSite plus HSTS together close the session-hijacking paths.",
      },
    ],
    finalAssessment: {
      question:
        "Combined assessment: across all five investigations, what single principle best unifies every fix you applied?",
      options: [
        { id: "a", label: "Add more client-side JavaScript validation" },
        {
          id: "b",
          label: "Never trust input or identity implicitly — verify and enforce controls server-side at every boundary",
        },
        { id: "c", label: "Rely on obscurity: hide IDs, versions and error messages" },
        { id: "d", label: "Encrypt everything and assume the rest is safe" },
      ],
      answer: "b",
      wrongFeedback:
        "Client validation and obscurity are helpful at best. The thread through auth, authz, input, config and HTTP is explicit, server-side verification at every trust boundary.",
      explanation:
        "Enumeration, IDOR, XSS, misconfiguration and weak cookies all stem from implicit trust. Verifying identity, ownership, input and configuration server-side is the unifying defence.",
    },
    question: "What is the most serious issue in this HTTP exchange?",
    options: [
      { id: "a", label: "The Server header reveals nginx 1.24.0" },
      {
        id: "b",
        label: "The session cookie lacks Secure, HttpOnly and SameSite attributes",
      },
      { id: "c", label: "Cache-Control is set to no-store" },
      { id: "d", label: "The request uses GET instead of POST" },
    ],
    answer: "b",
    wrongFeedback:
      "Version disclosure is minor and no-store is actually correct. Look at how the session cookie is set — its missing attributes are what enable session hijacking.",
    baseScore: 200,
    outcome: {
      discovered:
        "The session cookie was issued without Secure, HttpOnly, or SameSite flags, and key security headers (HSTS, X-Content-Type-Options) were absent.",
      whyItMatters:
        "An unprotected session cookie can be stolen over plaintext, read by injected JavaScript, or sent cross-site — leading directly to full account takeover.",
      secureApproach:
        "Set session cookies with Secure; HttpOnly; SameSite=Strict, enforce HSTS, and add X-Content-Type-Options: nosniff. Treat headers as part of the security surface.",
      nextSkill: "You've completed the core path. Revisit any lab to raise your score and skill matrix.",
    },
  },
];

/** Stable key under which a lab's final-assessment progress is stored. */
export const FINAL_STEP_ID = "__final__";

/** Standardized scoring: base 100, −3 per wrong attempt, −5 per hint, floor 60. */
export const SCORE_BASE = 100;
export const SCORE_PER_WRONG = 3;
export const SCORE_PER_HINT = 5;
export const SCORE_FLOOR = 60;

export function computeScore(wrongAttempts: number, hintsUsed: number): number {
  return Math.max(
    SCORE_FLOOR,
    SCORE_BASE - wrongAttempts * SCORE_PER_WRONG - hintsUsed * SCORE_PER_HINT,
  );
}

/** Decide-steps (plus the final assessment) that gate completion for a lab. */
export function decideStepIds(lab: Lab): string[] {
  const ids = (lab.steps ?? []).filter((s) => s.kind === "decide").map((s) => s.id);
  if (lab.finalAssessment) ids.push(FINAL_STEP_ID);
  return ids;
}

export function getLab(id: string): Lab | undefined {
  return LABS.find((l) => l.id === id);
}

/** Skill matrix axes derived from lab categories. */
export const SKILL_AXES = [
  { key: "Identity", labs: ["auth"] },
  { key: "Access Control", labs: ["authz"] },
  { key: "Injection", labs: ["input"] },
  { key: "Hardening", labs: ["config"] },
  { key: "Traffic", labs: ["http"] },
] as const;
