import { useEffect } from "react";
import { useApp } from "../context/AppContext";
import { ACHIEVEMENTS } from "../lib/achievements";
import { Icon } from "./ui/Icon";
import type { IconName } from "./ui/Icon";

const ACH_ICON: Record<string, IconName> = {
  flag: "flag",
  shield: "shield",
  zap: "zap",
  target: "target",
  crown: "crown",
  eye: "eye",
};

export function AchievementToast() {
  const { newlyUnlocked, clearUnlocked } = useApp();

  useEffect(() => {
    if (newlyUnlocked.length === 0) return;
    const t = setTimeout(clearUnlocked, 4200);
    return () => clearTimeout(t);
  }, [newlyUnlocked, clearUnlocked]);

  if (newlyUnlocked.length === 0) return null;

  return (
    <div
      className="pointer-events-none fixed bottom-6 right-6 z-[60] flex flex-col gap-3"
      role="status"
      aria-live="polite"
    >
      {newlyUnlocked.map((id) => {
        const a = ACHIEVEMENTS.find((x) => x.id === id);
        if (!a) return null;
        return (
          <div
            key={id}
            className="animate-toast-in pointer-events-auto flex items-center gap-3 rounded-2xl border border-cyan/30 bg-card/95 p-4 pr-6 shadow-2xl backdrop-blur glow-cyan"
          >
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-cyan/15 text-cyan">
              <Icon name={ACH_ICON[a.icon]} size={22} />
            </span>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-cyan">
                Achievement unlocked
              </div>
              <div className="text-sm font-semibold text-foreground">{a.title}</div>
              <div className="text-xs text-muted-foreground">{a.description}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
