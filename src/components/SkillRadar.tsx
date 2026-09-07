import { useApp } from "../context/AppContext";
import { SKILL_AXES } from "../lib/labs";
import { useInView } from "./ui/primitives";

/**
 * SVG skill radar. Each axis maps to a lab category; the filled area reflects the
 * learner's score on the associated lab (normalised to that lab's base score).
 */
export function SkillRadar({ size = 300 }: { size?: number }) {
  const { state } = useApp();
  const { ref, inView } = useInView<SVGSVGElement>({ threshold: 0.3 });
  const cx = size / 2;
  const cy = size / 2;
  const R = size / 2 - 44;
  const axes = SKILL_AXES;
  const n = axes.length;

  const values = axes.map((axis) => {
    const labId = axis.labs[0];
    const p = state.labs[labId];
    if (!p) return 0;
    if (p.status === "completed") return Math.min(1, 0.55 + (p.score / 240) * 0.9);
    if (p.status === "in-progress") return 0.35;
    if (p.status === "available") return 0.12;
    return 0.06;
  });

  const point = (i: number, r: number) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [cx + Math.cos(angle) * r, cy + Math.sin(angle) * r] as const;
  };

  const rings = [0.25, 0.5, 0.75, 1];
  const dataPath =
    values
      .map((v, i) => {
        const [x, y] = point(i, R * Math.max(0.05, v));
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ") + " Z";

  return (
    <svg ref={ref} width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="mx-auto">
      {rings.map((rr, i) => (
        <polygon
          key={i}
          points={axes
            .map((_, idx) => point(idx, R * rr).join(","))
            .join(" ")}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={1}
        />
      ))}
      {axes.map((_, i) => {
        const [x, y] = point(i, R);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--color-border)" strokeWidth={1} />;
      })}

      <g
        style={{
          transformOrigin: `${cx}px ${cy}px`,
          transform: inView ? "scale(1)" : "scale(0.05)",
          opacity: inView ? 1 : 0,
          transition: "transform 1s cubic-bezier(0.22,1,0.36,1), opacity 0.8s ease",
        }}
      >
        <path
          d={dataPath}
          fill="rgba(34,211,238,0.16)"
          stroke="#22d3ee"
          strokeWidth={2}
          strokeLinejoin="round"
          style={{ filter: "drop-shadow(0 0 8px rgba(34,211,238,0.4))" }}
        />
        {values.map((v, i) => {
          const [x, y] = point(i, R * Math.max(0.05, v));
          return <circle key={i} cx={x} cy={y} r={3.2} fill="#a9f0ff" />;
        })}
      </g>

      {axes.map((axis, i) => {
        const [x, y] = point(i, R + 22);
        return (
          <text
            key={axis.key}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="font-mono"
            fontSize={10}
            fill="var(--color-muted-foreground)"
            style={{ textTransform: "uppercase", letterSpacing: "0.1em" }}
          >
            {axis.key}
          </text>
        );
      })}
    </svg>
  );
}
