import { useEffect, useRef } from "react";
import { usePrefersReducedMotion } from "../../context/AppContext";

interface Piece {
  x: number;
  y: number;
  vx: number;
  vy: number;
  rot: number;
  vr: number;
  size: number;
  color: string;
  life: number;
}

const COLORS = ["#22d3ee", "#2f6bff", "#8b5cf6", "#34d399", "#e7edf7"];

/** One-shot canvas confetti burst. Auto-cleans; skipped under reduced-motion. */
export function Confetti() {
  const ref = useRef<HTMLCanvasElement | null>(null);
  const reduced = usePrefersReducedMotion();

  useEffect(() => {
    if (reduced) return;
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = (canvas.width = canvas.offsetWidth * dpr);
    const h = (canvas.height = canvas.offsetHeight * dpr);
    ctx.scale(dpr, dpr);
    const cw = canvas.offsetWidth;
    const ch = canvas.offsetHeight;

    const pieces: Piece[] = [];
    const count = 130;
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + Math.random() * 0.4;
      const speed = 3 + Math.random() * 7;
      pieces.push({
        x: cw / 2,
        y: ch * 0.32,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 3,
        rot: Math.random() * Math.PI,
        vr: (Math.random() - 0.5) * 0.3,
        size: 4 + Math.random() * 5,
        color: COLORS[i % COLORS.length],
        life: 1,
      });
    }

    let raf = 0;
    let frame = 0;
    const draw = () => {
      frame++;
      ctx.clearRect(0, 0, w, h);
      let alive = false;
      for (const p of pieces) {
        p.vy += 0.16;
        p.vx *= 0.99;
        p.x += p.vx;
        p.y += p.vy;
        p.rot += p.vr;
        if (frame > 60) p.life -= 0.012;
        if (p.life > 0 && p.y < ch + 20) alive = true;
        ctx.save();
        ctx.globalAlpha = Math.max(0, p.life);
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
        ctx.restore();
      }
      if (alive) raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [reduced]);

  if (reduced) return null;
  return (
    <canvas
      ref={ref}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-20 h-full w-full"
    />
  );
}
