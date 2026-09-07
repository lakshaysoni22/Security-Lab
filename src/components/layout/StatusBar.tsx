import React, { useEffect, useState } from 'react';
import { Cpu, Database, FileDigit, ShieldAlert, Check } from 'lucide-react';
import { useNavStore } from '../../stores';

export const StatusBar: React.FC = () => {
  const sidebarOpen = useNavStore((s) => s.sidebarOpen);
  const [blockHeight, setBlockHeight] = useState(19234567);
  const [syncStatus, setSyncStatus] = useState('Synchronized');
  const [activeJob, setActiveJob] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState(0);

  useEffect(() => {
    // Simulate block sync increments
    const syncInterval = setInterval(() => {
      setBlockHeight((prev) => prev + Math.floor(Math.random() * 3));
    }, 8000);

    // Simulate occasional background hashing/PDF jobs
    const jobs = [
      'Evidence Hashing (SHA-256 check)',
      'PDF Dossier Compile Pipeline',
      'Graph layout indexing (Cose algorithm)',
      'Watchlist database synchronization'
    ];

    const jobInterval = setInterval(() => {
      if (!activeJob) {
        const nextJob = jobs[Math.floor(Math.random() * jobs.length)];
        setActiveJob(nextJob);
        setJobProgress(0);
      }
    }, 15000);

    return () => {
      clearInterval(syncInterval);
      clearInterval(jobInterval);
    };
  }, [activeJob]);

  useEffect(() => {
    if (activeJob) {
      const progressInterval = setInterval(() => {
        setJobProgress((prev) => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            setTimeout(() => setActiveJob(null), 1000); // clear job shortly after done
            return 100;
          }
          return prev + Math.floor(Math.random() * 15) + 5;
        });
      }, 500);
      return () => clearInterval(progressInterval);
    }
  }, [activeJob]);

  return (
    <footer className={`fixed bottom-0 right-0 h-8 bg-dark-900 border-t border-dark-700/50 px-4 
      flex items-center justify-between text-[11px] text-dark-400 z-50 select-none transition-all duration-300
      ${sidebarOpen ? 'left-0 md:left-64' : 'left-0 md:left-[72px]'}`}
    >
      {/* Left side: Node Sync */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <Database size={12} className="text-accent-green" />
          <span>Block Height: <span className="mono text-white">{blockHeight.toLocaleString()}</span></span>
        </div>
        <span className="text-dark-700">|</span>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
          <span className="text-dark-300 font-semibold">{syncStatus}</span>
        </div>
      </div>

      {/* Center: Running jobs */}
      <div className="hidden md:flex flex-1 max-w-md mx-8 items-center justify-center">
        {activeJob ? (
          <div className="flex items-center gap-2.5 w-full">
            <Cpu size={12} className="text-accent-gold animate-spin" />
            <span className="truncate text-dark-300 max-w-[200px]">{activeJob}</span>
            <div className="flex-1 h-1 bg-dark-800 rounded overflow-hidden">
              <div 
                className="h-full bg-accent-gold transition-all duration-200" 
                style={{ width: `${jobProgress}%` }}
              />
            </div>
            <span className="mono text-accent-gold">{jobProgress}%</span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-dark-500">
            <Check size={12} />
            <span>All background worker engines idle</span>
          </div>
        )}
      </div>

      {/* Right side: Security context */}
      <div className="hidden sm:flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <FileDigit size={12} className="text-primary-400" />
          <span>Hash verify: <span className="text-dark-300 font-medium">Auto-active</span></span>
        </div>
        <span className="text-dark-700">|</span>
        <div className="flex items-center gap-1 text-dark-300 font-medium">
          <ShieldAlert size={12} className="text-primary-400" />
          <span>CC-Cell Gateway</span>
        </div>
      </div>
    </footer>
  );
};
