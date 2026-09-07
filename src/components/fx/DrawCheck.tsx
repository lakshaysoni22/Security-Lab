/** Animated SVG checkmark — circle + tick draw in via stroke-dasharray. */
export function DrawCheck({ size = 64, color = "#34d399" }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 52 52" aria-hidden="true">
      <circle
        cx="26"
        cy="26"
        r="24"
        fill="none"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        className="animate-draw"
        style={{ ["--len" as string]: 151 }}
      />
      <path
        d="M15 27 L23 35 L38 18"
        fill="none"
        stroke={color}
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="animate-draw"
        style={{ ["--len" as string]: 42, animationDelay: "0.5s" }}
      />
    </svg>
  );
}
