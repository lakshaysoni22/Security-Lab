import { useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import type { Route } from "../lib/types";
import { Icon } from "./ui/Icon";
import { PremiumButton, cx } from "./ui/primitives";

const NAV: Array<{ label: string; route: Route }> = [
  { label: "Home", route: { name: "home" } },
  { label: "Labs", route: { name: "labs" } },
  { label: "Resources", route: { name: "resources" } },
  { label: "Dashboard", route: { name: "dashboard" } },
];

// Secondary destinations — surfaced in the footer and the mobile menu so the
// desktop bar stays uncluttered.
const NAV_MORE: Array<{ label: string; route: Route }> = [
  { label: "Learning Path", route: { name: "learning" } },
  { label: "Progress", route: { name: "progress" } },
  { label: "Achievements", route: { name: "achievements" } },
  { label: "Safety", route: { name: "safety" } },
  { label: "About", route: { name: "about" } },
];

export function Navbar() {
  const { route, navigate, completedCount } = useApp();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  const onHero = route.name === "home" && !scrolled;
  const isActive = (r: Route) =>
    r.name === route.name || (r.name === "labs" && route.name === "lab");

  return (
    <header
      className={cx(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        onHero ? "bg-transparent" : "glass border-b border-border/80",
      )}
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-8">
        <button
          onClick={() => navigate({ name: "home" })}
          className="group flex items-center gap-2.5"
          aria-label="Cyber Labs home"
        >
          <span className="relative grid h-9 w-9 place-items-center rounded-lg bg-primary/15 text-cyan ring-1 ring-cyan/30">
            <Icon name="shield" size={20} />
            <span className="absolute inset-0 rounded-lg bg-cyan/10 blur-md transition-opacity group-hover:opacity-100 opacity-0" />
          </span>
          <span className="hidden sm:block">
            <span className="block font-display text-sm font-semibold leading-none tracking-wide text-foreground">
              CYBER LABS
            </span>
            <span className="block font-mono text-[10px] uppercase tracking-[0.25em] text-cyan/80">
              Security Platform
            </span>
          </span>
        </button>

        <div className="hidden items-center gap-1 md:flex">
          {NAV.map((item) => (
            <button
              key={item.label}
              onClick={() => navigate(item.route)}
              className={cx(
                "relative rounded-lg px-3.5 py-2 text-sm font-medium transition-colors",
                isActive(item.route)
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {item.label}
              {isActive(item.route) && (
                <span className="absolute inset-x-3 -bottom-0.5 h-px bg-gradient-to-r from-transparent via-cyan to-transparent" />
              )}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-1.5 rounded-lg bg-muted/60 px-2.5 py-1.5 font-mono text-xs text-muted-foreground sm:flex">
            <Icon name="check-circle" size={13} className="text-success" />
            {completedCount}/5
          </div>
          <PremiumButton
            size="sm"
            className="hidden sm:inline-flex"
            iconRight="arrow-right"
            onClick={() => navigate({ name: "labs" })}
          >
            Enter Labs
          </PremiumButton>
          <button
            className="grid h-10 w-10 place-items-center rounded-lg text-foreground md:hidden"
            onClick={() => setOpen((o) => !o)}
            aria-label="Toggle menu"
            aria-expanded={open}
          >
            <Icon name={open ? "x" : "menu"} size={22} />
          </button>
        </div>
      </nav>

      {open && (
        <div className="animate-slide-down glass border-t border-border/60 md:hidden">
          <div className="mx-auto max-w-7xl px-5 py-4">
            <div className="flex flex-col gap-1">
              {[...NAV, ...NAV_MORE].map((item) => (
                <button
                  key={item.label}
                  onClick={() => {
                    navigate(item.route);
                    setOpen(false);
                    window.scrollTo({ top: 0, behavior: "smooth" });
                  }}
                  className={cx(
                    "flex items-center justify-between rounded-lg px-3 py-3 text-left text-sm transition-colors active:bg-muted/50",
                    isActive(item.route)
                      ? "bg-muted text-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  {item.label}
                  <Icon name="chevron-right" size={16} />
                </button>
              ))}
              <PremiumButton
                className="mt-2"
                iconRight="arrow-right"
                onClick={() => {
                  navigate({ name: "labs" });
                  setOpen(false);
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
              >
                Enter Labs
              </PremiumButton>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
