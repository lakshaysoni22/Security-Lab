import { useEffect, useRef } from "react";
import { usePrefersReducedMotion } from "../../context/AppContext";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  hot: number; // highlight energy 0..1
}

/**
 * Lightweight Canvas 2D "security mesh" — a rotating field of glowing nodes with
 * proximity links and pointer parallax. No external 3D dependency; degrades to a
 * static render when reduced motion is requested.
 */
export function CyberNetwork() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const reduced = usePrefersReducedMotion();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let w = 0;
    let h = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    const nodes: Node[] = [];
    const pointer = { x: 0, y: 0, active: false };
    const parallax = { x: 0, y: 0 };
    let sweep = 0; // 0..1 position of the data-stream band

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      w = rect.width;
      h = rect.height;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      build();
    };

    const build = () => {
      nodes.length = 0;
      const count = Math.min(64, Math.max(26, Math.floor((w * h) / 12000)));
      for (let i = 0; i < count; i++) {
        nodes.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.18,
          vy: (Math.random() - 0.5) * 0.18,
          r: Math.random() * 1.8 + 1,
          hot: Math.random() * 0.3,
        });
      }
    };

    const onMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointer.x = e.clientX - rect.left;
      pointer.y = e.clientY - rect.top;
      pointer.active = true;
      parallax.x = (pointer.x / w - 0.5) * 26;
      parallax.y = (pointer.y / h - 0.5) * 26;
    };
    const onLeave = () => {
      pointer.active = false;
    };

    const LINK = 128;

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      ctx.save();
      ctx.translate(parallax.x, parallax.y);

      // links
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d = Math.hypot(dx, dy);
          if (d < LINK) {
            const alpha = (1 - d / LINK) * 0.5;
            const energy = Math.max(a.hot, b.hot);
            ctx.strokeStyle = `rgba(${34 + energy * 60}, ${211}, ${238}, ${alpha * (0.35 + energy)})`;
            ctx.lineWidth = 0.6 + energy * 0.8;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      // data-stream sweep — a faint bright band travelling left→right
      const sx = sweep * (w + 200) - 100;
      const grad = ctx.createLinearGradient(sx - 90, 0, sx + 90, 0);
      grad.addColorStop(0, "rgba(34,211,238,0)");
      grad.addColorStop(0.5, "rgba(34,211,238,0.10)");
      grad.addColorStop(1, "rgba(34,211,238,0)");
      ctx.fillStyle = grad;
      ctx.fillRect(sx - 90, 0, 180, h);

      // nodes
      for (const n of nodes) {
        const glow = 3 + n.hot * 9;
        ctx.beginPath();
        const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, glow);
        g.addColorStop(0, `rgba(120, 220, 255, ${0.8})`);
        g.addColorStop(1, "rgba(47, 107, 255, 0)");
        ctx.fillStyle = g;
        ctx.arc(n.x, n.y, glow, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.fillStyle = n.hot > 0.5 ? "#a9f0ff" : "#7fd4ff";
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    };

    const step = () => {
      for (const n of nodes) {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;

        // pointer excites nearby nodes
        if (pointer.active) {
          const d = Math.hypot(n.x - pointer.x, n.y - pointer.y);
          if (d < 140) n.hot = Math.min(1, n.hot + (1 - d / 140) * 0.08);
        }
        n.hot *= 0.96;
      }
      // ease parallax back toward rest
      if (!pointer.active) {
        parallax.x *= 0.95;
        parallax.y *= 0.95;
      }
      sweep += 0.0016;
      if (sweep > 1) sweep = 0;
      draw();
      raf = requestAnimationFrame(step);
    };

    resize();
    window.addEventListener("resize", resize);
    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerleave", onLeave);

    if (reduced) {
      draw();
    } else {
      raf = requestAnimationFrame(step);
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerleave", onLeave);
    };
  }, [reduced]);

  return <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" aria-hidden="true" />;
}
