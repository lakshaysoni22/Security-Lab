import React from 'react';
import { X, Keyboard } from 'lucide-react';

interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ShortcutsModal: React.FC<ShortcutsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const shortcutList = [
    { keys: ['Ctrl', 'K'], desc: 'Focus Global Search Box' },
    { keys: ['Ctrl', 'N'], desc: 'Open Create Case Modal' },
    { keys: ['Ctrl', 'E'], desc: 'Open Catalog Evidence Modal' },
    { keys: ['Ctrl', 'R'], desc: 'Switch to Report Exporter' },
    { keys: ['Ctrl', 'G'], desc: 'Switch to Graph Visualizer' },
    { keys: ['Ctrl', '/'], desc: 'Show Keyboard Shortcuts Reference' },
  ];

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-card w-full max-w-sm p-5 animate-scale-in border-primary-500/20">
        {/* Title */}
        <div className="flex items-center justify-between border-b border-dark-700/50 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Keyboard size={16} className="text-primary-400" />
            <h3 className="text-sm font-bold text-white">Keyboard Shortcuts</h3>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded text-dark-400 hover:text-white hover:bg-dark-800 transition-colors"
          >
            <X size={14} />
          </button>
        </div>

        {/* Shortcuts */}
        <div className="space-y-2.5">
          {shortcutList.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between text-xs">
              <span className="text-dark-300">{item.desc}</span>
              <div className="flex items-center gap-1">
                {item.keys.map((k) => (
                  <kbd 
                    key={k} 
                    className="px-1.5 py-0.5 bg-dark-900 border border-dark-750 text-white rounded font-mono font-semibold text-[10px]"
                  >
                    {k}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Help footer */}
        <p className="text-[10px] text-dark-500 text-center mt-5 border-t border-dark-700/50 pt-3">
          Shortcuts are active on all platform pages
        </p>
      </div>
    </div>
  );
};
