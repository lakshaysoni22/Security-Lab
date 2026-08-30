import { useApp } from "../context/AppContext";
import type { Lab } from "../lib/types";
import { Icon } from "./ui/Icon";
import type { IconName } from "./ui/Icon";
import {
  Chip,
  DifficultyBadge,
  GlowCard,
  ProgressBar,
  StatusBadge,
  accentHex,
  accentText,
  cx,
} from "./ui/primitives";

const LAB_ICON: Record<string, IconName> = {
  auth: "fingerprint",
  authz: "key",
  input: "code",
  config: "server",
  http: "globe",
};

export function LabCard({ lab }: { lab: Lab }) {
  const { navigate, labProgress } = useApp();
  const p = labProgress(lab.id);
  const locked = p.status === "locked";
  const completed = p.status === "completed";
  const pct = completed ? 100 : p.status === "in-progress" ? 50 : 0;

  return (
    <GlowCard accent={lab.accent} interactive={!locked} className={cx(locked && "opacity-70")}>
      <button
        onClick={() => !locked && navigate({ name: "lab", labId: lab.id })}
        disabled={locked}
        className="block w-full p-6 text-left disabled:cursor-not-allowed"
      >
        {/* top row */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <span
              className={cx(
                "grid h-12 w-12 place-items-center rounded-xl ring-1",
                accentText(lab.accent),
              )}
              style={{
                background: `color-mix(in srgb, ${accentHex(lab.accent)} 12%, transparent)`,
                borderColor: "transparent",
                boxShadow: `inset 0 0 0 1px color-mix(in srgb, ${accentHex(lab.accent)} 30%, transparent)`,
              }}
            >
              <Icon name={locked ? "lock" : LAB_ICON[lab.id]} size={22} />
            </span>
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-subtle">
                Lab {String(lab.number).padStart(2, "0")} · {lab.category}
              </div>
              <h3 className="mt-0.5 text-lg font-semibold text-foreground">{lab.title}</h3>
            </div>
          </div>
          <StatusBadge status={p.status} />
        </div>

        <p className="mt-4 text-sm leading-relaxed text-muted-foreground">{lab.summary}</p>

        {/* skills */}
        <div className="mt-4 flex flex-wrap gap-1.5">
          {lab.skills.map((s) => (
            <Chip key={s}>{s}</Chip>
          ))}
        </div>

        {/* meta */}
        <div className="mt-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <DifficultyBadge level={lab.difficulty} />
            <Chip icon="clock">{lab.estMinutes} min</Chip>
          </div>
          {!locked && (
            <span className={cx("flex items-center gap-1.5 text-sm font-medium", accentText(lab.accent))}>
              {completed ? "Review" : p.status === "in-progress" ? "Resume" : "Begin"}
              <Icon name="arrow-right" size={16} />
            </span>
          )}
        </div>

        {(pct > 0 || completed) && (
          <div className="mt-4">
            <ProgressBar value={pct} accent={lab.accent} />
            {completed && (
              <div className="mt-2 flex items-center justify-between font-mono text-[11px] text-muted-foreground">
                <span>Score {p.score}</span>
                <span>{p.hintsUsed} hints · {p.attempts} attempts</span>
              </div>
            )}
          </div>
        )}

        {locked && (
          <div className="mt-4 flex items-center gap-2 font-mono text-[11px] text-subtle">
            <Icon name="lock" size={13} /> Complete the previous lab to unlock
          </div>
        )}
      </button>
    </GlowCard>
  );
}
