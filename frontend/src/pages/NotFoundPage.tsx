import React, { useEffect, useState } from 'react';
import { ArrowLeft, RefreshCw, WifiOff } from 'lucide-react';
import { useNavStore } from '../stores';

interface SpaceErrorPageProps {
  errorTitle?: string;
  errorMessage?: string;
  onRetry?: () => void;
}

export const NotFoundPage: React.FC<SpaceErrorPageProps> = ({
  errorTitle = 'Lost in space',
  errorMessage = "The page or connection you're looking for has drifted out of orbit — it doesn't exist, is offline, or network signal was lost.",
  onRetry
}) => {
  const { setPage } = useNavStore();
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 20;
      const y = (e.clientY / window.innerHeight - 0.5) * 20;
      setMousePos({ x, y });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-[100dvh] w-full bg-dark-950 grid-bg flex flex-col items-center justify-center p-4 sm:p-8 relative overflow-hidden text-white select-none">
      {/* Background Starfield & Space Gradient */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/5 w-80 h-80 bg-primary-500/10 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-purple/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1.5s' }} />

        {/* Planet sphere in bottom left */}
        <div
          className="absolute -bottom-24 -left-24 w-80 h-80 rounded-full bg-gradient-to-tr from-cyan-900/40 via-dark-900 to-transparent border border-primary-500/20 shadow-[0_0_60px_rgba(0,212,255,0.15)] opacity-60"
          style={{ transform: `translate(${mousePos.x * -0.5}px, ${mousePos.y * -0.5}px)` }}
        />

        {/* Floating stars */}
        <div className="absolute top-12 left-1/3 w-1.5 h-1.5 bg-white rounded-full animate-ping opacity-75" />
        <div className="absolute top-1/3 right-1/5 w-2 h-2 bg-primary-400 rounded-full animate-pulse" />
        <div className="absolute bottom-1/3 left-1/4 w-1 h-1 bg-white rounded-full opacity-50" />
      </div>

      {/* Main Card Content */}
      <div className="relative z-10 max-w-lg w-full text-center space-y-6 animate-slide-up">
        {/* Header Tag */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-dark-900/80 border border-primary-500/30 text-[10px] uppercase font-mono tracking-widest text-primary-300 shadow-md">
          <WifiOff size={12} className="text-accent-gold" />
          <span>LOST IN SPACE · ERROR 404</span>
        </div>

        {/* 404 Space Hero Circle */}
        <div
          className="relative my-4 flex items-center justify-center gap-4 sm:gap-6 py-6"
          style={{ transform: `translate(${mousePos.x * 0.3}px, ${mousePos.y * 0.3}px)` }}
        >
          {/* Left Digit 4 */}
          <span className="text-6xl sm:text-8xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-cyan-100 via-primary-300 to-primary-600 drop-shadow-[0_0_25px_rgba(0,212,255,0.6)] font-mono">
            4
          </span>

          {/* Glowing Orbital Ring with Astronaut inside */}
          <div className="relative w-36 h-36 sm:w-44 sm:h-44 flex items-center justify-center">
            {/* Outer Rotating Glowing Orbit Ring */}
            <div className="absolute inset-0 rounded-full border-4 border-t-primary-400 border-r-primary-500/30 border-b-cyan-300 border-l-primary-500/40 shadow-[0_0_45px_rgba(0,212,255,0.4)] animate-spin" style={{ animationDuration: '18s' }} />

            {/* Orbit Beacon Dot */}
            <div className="absolute -top-1.5 right-6 w-3.5 h-3.5 bg-accent-red rounded-full shadow-[0_0_12px_#ff3366] animate-pulse" />

            {/* Floating Astronaut SVG */}
            <div className="relative z-10 animate-bounce" style={{ animationDuration: '4s' }}>
              <svg className="w-20 h-20 sm:w-24 sm:h-24 drop-shadow-[0_10px_20px_rgba(0,0,0,0.8)]" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Suit Outer */}
                <circle cx="50" cy="50" r="32" fill="#0A0E1A" stroke="#00D4FF" strokeWidth="4" />
                {/* Visor Glass */}
                <ellipse cx="50" cy="46" rx="20" ry="15" fill="#00D4FF" fillOpacity="0.85" stroke="#FFFFFF" strokeWidth="2" />
                {/* Visor Reflection */}
                <ellipse cx="44" cy="42" rx="6" ry="4" fill="#FFFFFF" fillOpacity="0.7" />
                {/* Chest Control Box */}
                <rect x="42" y="66" width="16" height="12" rx="3" fill="#1E293B" stroke="#00D4FF" strokeWidth="1.5" />
                <circle cx="46" cy="72" r="2" fill="#FF3366" />
                <circle cx="54" cy="72" r="2" fill="#00D4FF" />
                {/* Oxygen Tether Wire */}
                <path d="M 68 62 Q 85 75 75 90" stroke="#00D4FF" strokeWidth="2.5" strokeDasharray="3 3" fill="none" />
                <circle cx="75" cy="90" r="3" fill="#00D4FF" />
              </svg>
            </div>
          </div>

          {/* Right Digit 4 */}
          <span className="text-6xl sm:text-8xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-cyan-100 via-primary-300 to-primary-600 drop-shadow-[0_0_25px_rgba(0,212,255,0.6)] font-mono">
            4
          </span>
        </div>

        {/* Text & Message */}
        <div className="space-y-2">
          <p className="text-xs uppercase font-mono tracking-widest text-primary-400 font-bold">ERROR 404</p>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">{errorTitle}</h1>
          <p className="text-xs sm:text-sm text-dark-300 max-w-md mx-auto leading-relaxed">
            {errorMessage}
          </p>
        </div>

        {/* Action Button */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => {
              if (onRetry) {
                onRetry();
              } else {
                setPage('dashboard');
              }
            }}
            className="px-8 py-3 rounded-full border-2 border-white/90 hover:border-primary-400 bg-dark-900/80 hover:bg-primary-500/20 text-white font-bold text-sm tracking-wide transition-all shadow-lg hover:shadow-glow-cyan active:scale-95 flex items-center justify-center gap-2 cursor-pointer"
          >
            <ArrowLeft size={16} />
            <span>Take me home</span>
          </button>

          {onRetry && (
            <button
              onClick={onRetry}
              className="px-6 py-3 rounded-full bg-primary-500 hover:bg-primary-400 text-white font-bold text-sm transition-all shadow-glow-cyan active:scale-95 flex items-center justify-center gap-2 cursor-pointer"
            >
              <RefreshCw size={16} />
              <span>Retry Connection</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
