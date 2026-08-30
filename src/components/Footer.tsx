import { useApp } from "../context/AppContext";
import type { Route } from "../lib/types";
import { Icon } from "./ui/Icon";

const COLS: Array<{ title: string; links: Array<{ label: string; route: Route }> }> = [
  {
    title: "Platform",
    links: [
      { label: "Labs", route: { name: "labs" } },
      { label: "Learning Path", route: { name: "learning" } },
      { label: "Dashboard", route: { name: "dashboard" } },
      { label: "Progress", route: { name: "progress" } },
      { label: "Achievements", route: { name: "achievements" } },
    ],
  },
  {
    title: "Learn & Trust",
    links: [
      { label: "Reference", route: { name: "resources" } },
      { label: "Safety Model", route: { name: "safety" } },
      { label: "About", route: { name: "about" } },
      { label: "Overview", route: { name: "home" } },
    ],
  },
];

export function Footer() {
  const { navigate } = useApp();
  return (
    <footer className="relative border-t border-border/70 bg-surface">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:gap-10 sm:px-8 sm:py-14 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary/15 text-cyan ring-1 ring-cyan/30">
              <Icon name="shield" size={20} />
            </span>
            <span>
              <span className="block font-display text-sm font-semibold tracking-wide">
                CYBER LABS
              </span>
              <span className="block font-mono text-[10px] uppercase tracking-[0.25em] text-cyan/80">
                Security Platform
              </span>
            </span>
          </div>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-foreground">
            Hands-on cybersecurity training and interactive defense simulations. Learn to think
            like a defender through safe, guided investigations.
          </p>
          <div className="mt-5 inline-flex items-center gap-2 rounded-lg bg-success/10 px-3 py-1.5 font-mono text-xs text-success">
            <span className="h-1.5 w-1.5 rounded-full bg-success" style={{ animation: "pulse-ring 2s infinite" }} />
            All systems operational · Safe simulation
          </div>
        </div>

        {COLS.map((col) => (
          <div key={col.title}>
            <h4 className="font-mono text-xs uppercase tracking-[0.25em] text-subtle">
              {col.title}
            </h4>
            <ul className="mt-4 space-y-2.5">
              {col.links.map((l) => (
                <li key={l.label}>
                  <button
                    onClick={() => navigate(l.route)}
                    className="text-sm text-muted-foreground transition-colors hover:text-cyan"
                  >
                    {l.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-border/60">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 px-5 py-5 text-xs text-subtle sm:flex-row sm:px-8">
          <span className="font-mono">© 2026 Cyber Labs · Educational use only</span>
          <span className="font-mono">Built for defenders in training</span>
        </div>
      </div>
    </footer>
  );
}
