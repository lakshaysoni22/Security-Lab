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
 * Ultra-optimized Canvas 2D "security mesh" with auto-pause on scroll.
 * Uses IntersectionObserver so no CPU/GPU cycles are wasted when off-screen.
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
    let isVisible = true;
    const nodes: Node[] = [];
    const pointer = { x: 0, y: 0, active: false };
    const parallax = { x: 0, y: 0 };
    let sweep = 0;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      w = rect.width;
      h = rect.height;
      if (w === 0 || h === 0) return;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      build();
    };

    const build = () => {
      nodes.length = 0;
      // Adaptive node count based on viewport size for maximum mobile performance
      const isMobile = window.innerWidth < 768;
      const count = isMobile
        ? Math.min(28, Math.max(16, Math.floor((w * h) / 20000)))
        : Math.min(48, Math.max(24, Math.floor((w * h) / 14000)));

      for (let i = 0; i < count; i++) {
        nodes.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.16,
          vy: (Math.random() - 0.5) * 0.16,
          r: Math.random() * 1.5 + 0.8,
          hot: Math.random() * 0.2,
        });
      }
    };

    const onMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointer.x = e.clientX - rect.left;
      pointer.y = e.clientY - rect.top;
      pointer.active = true;
      parallax.x = (pointer.x / w - 0.5) * 20;
      parallax.y = (pointer.y / h - 0.5) * 20;
    };

    const onLeave = () => {
      pointer.active = false;
    };

    const LINK = window.innerWidth < 768 ? 96 : 120;

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      ctx.save();
      ctx.translate(parallax.x, parallax.y);

      // Links between proximate nodes
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d = Math.hypot(dx, dy);
          if (d < LINK) {
            const alpha = (1 - d / LINK) * 0.4;
            const energy = Math.max(a.hot, b.hot);
            ctx.strokeStyle = `rgba(34, 211, 238, ${alpha * (0.3 + energy)})`;
            ctx.lineWidth = 0.5 + energy * 0.6;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      // Nodes
      for (const n of nodes) {
        ctx.fillStyle = n.hot > 0.4 ? "#22d3ee" : "#2f6bff";
        ctx.shadowColor = "#22d3ee";
        ctx.shadowBlur = n.hot > 0.4 ? 8 : 0;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r + n.hot * 1.2, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();
    };

    const step = () => {
      if (!isVisible) return; // Paused when off-screen

      for (const n of nodes) {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;

        if (pointer.active) {
          const d = Math.hypot(n.x - pointer.x, n.y - pointer.y);
          if (d < 120) n.hot = Math.min(1, n.hot + (1 - d / 120) * 0.06);
        }
        n.hot *= 0.96;
      }

      if (!pointer.active) {
        parallax.x *= 0.95;
        parallax.y *= 0.95;
      }

      sweep += 0.0015;
      if (sweep > 1) sweep = 0;

      draw();
      raf = requestAnimationFrame(step);
    };

    // IntersectionObserver to stop RAF loop when hero is scrolled out of view
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        isVisible = entry?.isIntersecting ?? false;
        if (isVisible && !reduced) {
          cancelAnimationFrame(raf);
          raf = requestAnimationFrame(step);
        } else {
          cancelAnimationFrame(raf);
        }
      },
      { threshold: 0.05 }
    );

    observer.observe(canvas);
    resize();

    window.addEventListener("resize", resize, { passive: true });
    canvas.addEventListener("pointermove", onMove, { passive: true });
    canvas.addEventListener("pointerleave", onLeave, { passive: true });

    if (reduced) {
      draw();
    } else {
      raf = requestAnimationFrame(step);
    }

    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerleave", onLeave);
    };
  }, [reduced]);

  return <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" aria-hidden="true" />;
}
