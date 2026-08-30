import { useApp } from "../context/AppContext";
import { Icon } from "../components/ui/Icon";
import { PremiumButton, Reveal, SectionHeader } from "../components/ui/primitives";

export function Privacy() {
  const { navigate } = useApp();

  const sections = [
    {
      icon: "shield" as const,
      title: "Information We Collect",
      content:
        "Cyber Labs does not collect, store, or transmit any personal information. We do not require user registration, login credentials, email addresses, or any form of personally identifiable information (PII). The platform operates entirely within your browser with zero server-side data processing.",
    },
    {
      icon: "cookie" as const,
      title: "Cookies & Local Storage",
      content:
        "Cyber Labs does not use HTTP cookies. Your lab progress, scores, and achievements are stored locally in your browser's localStorage under the key 'cyber-labs.v1'. This data never leaves your device, is not transmitted to any server, and is fully under your control. You can clear this data at any time through your browser settings or the Dashboard reset option.",
    },
    {
      icon: "eye" as const,
      title: "Analytics & Tracking",
      content:
        "We do not use any analytics, tracking, or monitoring tools. There is no Google Analytics, Mixpanel, Hotjar, Facebook Pixel, or any similar service integrated into this platform. Your browsing behavior, interaction patterns, and usage data are not collected or analyzed by any party.",
    },
    {
      icon: "globe" as const,
      title: "Third-Party Services",
      content:
        "Cyber Labs loads Google Fonts (Inter, JetBrains Mono) for typography. This is the only external resource fetched by the application. No other third-party services, APIs, CDNs, or external scripts are loaded. The application makes zero API calls during normal usage.",
    },
    {
      icon: "lock" as const,
      title: "Data Security",
      content:
        "All lab simulations run entirely client-side within your browser's sandbox. No real network requests are made to external targets. No credentials, tokens, or sensitive data are transmitted. The platform is served over HTTPS with TLS encryption. Security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy) are enforced at the CDN level.",
    },
    {
      icon: "zap" as const,
      title: "Children's Privacy",
      content:
        "Cyber Labs is an educational platform designed for cybersecurity learning. We do not knowingly collect information from children under 13. Since we collect no personal information from any user, this policy applies universally regardless of age.",
    },
    {
      icon: "key" as const,
      title: "Your Rights & Control",
      content:
        "Since all data is stored locally in your browser, you have complete control over it. You can view your stored data by opening browser DevTools → Application → Local Storage. You can delete all progress data by clicking the 'Reset Progress' button on the Dashboard page, or by clearing your browser's local storage. No request to any server is required.",
    },
    {
      icon: "activity" as const,
      title: "Changes to This Policy",
      content:
        "If we make changes to this privacy policy, the updated version will be posted on this page with a revised date. Since we do not collect email addresses, we cannot send direct notifications — please review this page periodically.",
    },
  ];

  return (
    <div className="mx-auto max-w-4xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <Reveal>
        <SectionHeader
          eyebrow="Legal"
          title="Privacy Policy"
          description="Your privacy matters. Cyber Labs is designed with a privacy-first architecture — we collect zero personal data."
        />
      </Reveal>

      <Reveal delay={80}>
        <div className="mt-6 inline-flex items-center gap-2 rounded-lg bg-success/10 px-4 py-2 font-mono text-xs text-success">
          <Icon name="shield" size={14} />
          Zero data collection · No cookies · No tracking · 100% client-side
        </div>
      </Reveal>

      <div className="mt-10 space-y-6">
        {sections.map((s, i) => (
          <Reveal key={s.title} delay={i * 40}>
            <div className="rounded-2xl border border-border bg-card p-6">
              <div className="flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-cyan/10 text-cyan">
                  <Icon name={s.icon} size={18} />
                </span>
                <h3 className="text-base font-semibold text-foreground">{s.title}</h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{s.content}</p>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal delay={400}>
        <div className="mt-10 rounded-2xl border border-border bg-surface p-6 text-center">
          <p className="font-mono text-xs uppercase tracking-widest text-subtle">Last Updated</p>
          <p className="mt-1 text-sm text-muted-foreground">30 August 2026</p>
          <p className="mt-4 text-sm text-muted-foreground">
            Questions about this policy? This platform is maintained by Cyber Labs for educational purposes.
          </p>
          <PremiumButton className="mt-5" icon="arrow-right" onClick={() => navigate({ name: "home" })}>
            Back to Home
          </PremiumButton>
        </div>
      </Reveal>
    </div>
  );
}
