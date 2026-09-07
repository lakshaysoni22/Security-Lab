import React, { useState, useRef, useEffect } from 'react';
import { useNavStore, useAlertStore, useAuthStore, useBlockchainStore, useCaseStore } from '../../stores';
import { useInvestigationStore } from '../../stores/investigation';
import { Bell, Search, Wifi, Shield, X, FolderPlus, FileUp, Sparkles, Keyboard, Menu, Target } from 'lucide-react';
import { timeAgo, getSeverityColor } from '../../utils/helpers';

export const Header: React.FC = () => {
  const { sidebarOpen, currentPage, toggleSidebar, setPage, showShortcuts, setShowShortcuts } = useNavStore();
  const { alerts, markRead, markAllRead } = useAlertStore();
  const { user } = useAuthStore();
  const { activeTargetAddress } = useInvestigationStore();
  const { setSearchAddress } = useBlockchainStore();
  const { cases, selectCase } = useCaseStore();

  const [showAlerts, setShowAlerts] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  const alertRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const unreadCount = alerts.filter((a) => !a.isRead).length;

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (alertRef.current && !alertRef.current.contains(e.target as Node)) {
        setShowAlerts(false);
      }
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const pageTitle: Record<string, string> = {
    dashboard: 'Intelligence Dashboard',
    cases: 'Case Management',
    blockchain: 'Blockchain Analysis',
    graph: 'Transaction Graph',
    evidence: 'Evidence Vault',
    watchlist: 'Watchlist Monitor',
    alerts: 'Alert Center',
    reports: 'Report Generation',
    ai: 'Cyber Analysis Workspace',
    entities: 'Entity Intelligence',
    audit: 'Audit Trail',
    settings: 'Platform Settings',
    incident: 'Incident Response',
  };

  // Hardcoded search targets for immediate suggestion
  const searchTargets = [
    { type: 'case', label: 'GainChain Network Ponzi', id: 'case-1', chain: 'ETH', target: '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28' },
    { type: 'case', label: 'MedLock Ransomware', id: 'case-2', chain: 'BTC', target: '1LbcPeel5s9zARansom993vX78cDf' },
    { type: 'wallet', label: 'LockBit Ransomware Receiver (BTC)', target: '1LbcPeel5s9zARansom993vX78cDf', chain: 'BTC' },
    { type: 'wallet', label: 'Tornado Cash Exploit Drainer (ETH)', target: '0x71c20e241775e5332f143715df332f143789a71b', chain: 'ETH' },
    { type: 'wallet', label: 'GainChain Suspect (ETH)', target: '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28', chain: 'ETH' }
  ];

  const suggestions = searchQuery.trim() 
    ? searchTargets.filter(item => 
        item.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.target.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    useInvestigationStore.getState().setActiveTarget(searchQuery.trim());
    setSearchQuery('');
    setShowSuggestions(false);
  };

  const handleSuggestionClick = (item: any) => {
    setSearchQuery('');
    setShowSuggestions(false);
    useInvestigationStore.getState().setActiveTarget(item.target);
  };

  return (
    <header className={`fixed top-0 right-0 h-16 bg-dark-900/80 backdrop-blur-xl border-b border-dark-700/50 
      flex items-center justify-between px-4 md:px-6 z-[100] transition-snappy gpu-accelerated left-0
      ${sidebarOpen ? 'md:left-64' : 'md:left-[72px]'}`}
    >
      {/* Left */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="md:hidden p-2 rounded-lg bg-dark-800 border border-dark-700/50 hover:bg-dark-700 text-dark-300 hover:text-white transition-colors cursor-pointer"
        >
          <Menu size={16} />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base md:text-lg font-semibold text-white truncate max-w-[160px] md:max-w-none">{pageTitle[currentPage] || 'Dashboard'}</h2>
            <div className="hidden lg:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-primary-500/10 border border-primary-500/30 text-[11px] font-mono text-primary-300">
              <Target size={11} className="text-primary-400 animate-pulse" />
              <span>TARGET: {activeTargetAddress.slice(0, 8)}...{activeTargetAddress.slice(-6)}</span>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2 text-[10px] text-dark-400">
            <span className="flex items-center gap-1"><Wifi size={10} className="text-accent-green" /> CONNECTED</span>
            <span>•</span>
            <span className="flex items-center gap-1"><Shield size={10} className="text-primary-400" /> SECURE SESSION</span>
            <span>•</span>
            <span>{user?.department || 'Cyber Crime Cell'}</span>
          </div>
        </div>
      </div>

      {/* Center — Target Address Search Bar */}
      <div className="flex-1 max-w-md mx-2 sm:mx-8 relative" ref={searchRef}>
        <form onSubmit={handleSearchSubmit} className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
          <input
            id="global-search-input"
            type="text"
            placeholder="Enter target BTC/Crypto address (e.g. 1A1zP1...)..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            className="input-field pl-9 pr-7 py-1.5 sm:py-2 text-xs sm:text-sm w-full font-mono"
          />
          {searchQuery && (
            <button 
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white p-1"
            >
              <X size={14} />
            </button>
          )}
        </form>

        {/* Suggestions Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute left-0 right-0 top-12 glass-card bg-dark-900/98 max-h-60 overflow-y-auto z-[120] border-dark-700/50 shadow-2xl rounded-xl">
            {suggestions.map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(item)}
                className="w-full text-left px-3 sm:px-4 py-2.5 border-b border-dark-800/50 hover:bg-dark-800/60 transition-colors flex items-center justify-between text-xs cursor-pointer"
              >
                <div className="min-w-0 flex-1 pr-2">
                  <span className="font-semibold text-white truncate block">{item.label}</span>
                  <p className="text-[10px] text-dark-400 mono truncate mt-0.5">{item.target}</p>
                </div>
                <span className="px-2 py-0.5 rounded text-[9px] bg-dark-800 border border-dark-700 text-primary-400 capitalize font-bold flex-shrink-0">
                  {item.type}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right: Quick actions, Status, Alerts */}
      <div className="flex items-center gap-3">
        {/* Quick Actions Shortcuts */}
        <div className="hidden sm:flex items-center bg-dark-800/40 border border-dark-700/50 rounded-lg p-0.5">
          <button 
            onClick={() => setPage('cases')}
            className="p-1.5 rounded hover:bg-dark-700/50 text-dark-400 hover:text-white transition-colors"
            title="Create Case"
          >
            <FolderPlus size={16} />
          </button>
          <button 
            onClick={() => setPage('evidence')}
            className="p-1.5 rounded hover:bg-dark-700/50 text-dark-400 hover:text-white transition-colors"
            title="Catalog Evidence"
          >
            <FileUp size={16} />
          </button>
          <button 
            onClick={() => setPage('ai')}
            className="p-1.5 rounded hover:bg-dark-700/50 text-dark-400 hover:text-white transition-colors"
            title="AI Investigation Workspace"
          >
            <Sparkles size={16} />
          </button>
          <button 
            onClick={() => setShowShortcuts(true)}
            className="p-1.5 rounded hover:bg-dark-700/50 text-dark-400 hover:text-white transition-colors"
            title="Keyboard Shortcuts Guide"
          >
            <Keyboard size={16} />
          </button>
        </div>

        {/* Live Status */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-800/60 border border-dark-700/50">
          <div className="pulse-dot bg-accent-green" />
          <span className="text-[11px] text-dark-300 font-medium">Mainnet Online</span>
        </div>

        {/* Alerts */}
        <div className="relative" ref={alertRef}>
          <button
            onClick={() => setShowAlerts(!showAlerts)}
            className="relative p-2 rounded-lg hover:bg-dark-700/50 text-dark-300 hover:text-white transition-colors cursor-pointer"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-accent-red rounded-full text-[10px] font-bold flex items-center justify-center text-white animate-pulse">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Alert Dropdown */}
          {showAlerts && (
            <div className="absolute right-0 top-12 w-96 glass-card bg-dark-950/98 rounded-xl overflow-hidden animate-scale-in shadow-2xl z-[120] border border-dark-700/50">
              <div className="flex items-center justify-between px-4 py-3 border-b border-dark-700/50">
                <h3 className="text-sm font-semibold text-white">Alerts</h3>
                <div className="flex items-center gap-2">
                  <button onClick={markAllRead} className="text-[11px] text-primary-400 hover:text-primary-300">Mark all read</button>
                  <button onClick={() => setShowAlerts(false)} className="p-1 rounded hover:bg-dark-700/50 text-dark-400">
                    <X size={14} />
                  </button>
                </div>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {alerts.slice(0, 5).map((alert) => (
                  <button
                    key={alert.id}
                    onClick={() => {
                      markRead(alert.id);
                      if (alert.address) {
                        handleSuggestionClick({ type: 'wallet', target: alert.address });
                      }
                      setShowAlerts(false);
                    }}
                    className={`w-full text-left px-4 py-3 border-b border-dark-800/50 hover:bg-dark-700/30 transition-colors
                      ${!alert.isRead ? 'bg-dark-800/30' : ''}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                        alert.severity === 'critical' ? 'bg-accent-red' :
                        alert.severity === 'high' ? 'bg-accent-gold' :
                        alert.severity === 'medium' ? 'bg-primary-400' : 'bg-accent-green'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className={`text-xs ${!alert.isRead ? 'text-white font-medium' : 'text-dark-300'}`}>
                          {alert.message}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-[10px] font-semibold uppercase ${getSeverityColor(alert.severity)}`}>
                            {alert.severity}
                          </span>
                          <span className="text-[10px] text-dark-500">{timeAgo(alert.createdAt)}</span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

    </header>
  );
};
