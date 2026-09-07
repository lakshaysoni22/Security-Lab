import React, { useState } from 'react';
import { useInvestigationStore } from '../stores/investigation';
import { useNavStore } from '../stores';
import { Eye, Wallet, ArrowUpRight, ArrowDownRight, ArrowLeftRight, ExternalLink, Search, Activity } from 'lucide-react';

export const WatchlistPage: React.FC = () => {
  const { activeTargetAddress, summary, counterparties, riskScore, riskLevel } = useInvestigationStore();
  const { setPage } = useNavStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [dirFilter, setDirFilter] = useState<'all' | 'inbound' | 'outbound' | 'both'>('all');

  const filtered = counterparties.filter(cp => {
    const matchesSearch = searchTerm === '' || cp.address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDir = dirFilter === 'all' || cp.direction === dirFilter;
    return matchesSearch && matchesDir;
  });

  const dirIcon = (dir: string) => {
    switch (dir) {
      case 'inbound': return <ArrowDownRight size={12} className="text-accent-green" />;
      case 'outbound': return <ArrowUpRight size={12} className="text-accent-red" />;
      default: return <ArrowLeftRight size={12} className="text-accent-gold" />;
    }
  };

  const dirColor = (dir: string) => {
    switch (dir) {
      case 'inbound': return 'bg-accent-green/20 text-accent-green border-accent-green/30';
      case 'outbound': return 'bg-accent-red/20 text-accent-red border-accent-red/30';
      default: return 'bg-accent-gold/20 text-accent-gold border-accent-gold/30';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Eye size={20} className="text-primary-400" />
            <h2 className="text-xl font-bold text-white">Watchlist & Counterparties</h2>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Wallet size={12} className="text-primary-400" />
            <span className="text-xs text-dark-400 mono">{activeTargetAddress.slice(0, 16)}…{activeTargetAddress.slice(-8)}</span>
            <span className="text-[10px] text-dark-500">•</span>
            <span className="text-xs text-dark-400">{counterparties.length} counterpart{counterparties.length !== 1 ? 'ies' : 'y'} detected</span>
          </div>
        </div>
      </div>

      {/* Active Target Card */}
      <div className="glass-card p-4 border border-primary-500/20 bg-primary-500/5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[10px] text-primary-400 uppercase font-bold mb-1">● Active Investigation Target</div>
            <code className="text-sm text-white mono">{activeTargetAddress}</code>
            <div className="flex items-center gap-3 mt-2 text-xs text-dark-400">
              <span>Balance: {summary ? `${(summary.confirmedBalance / 1e8).toFixed(4)} BTC` : '—'}</span>
              <span>Txns: {summary?.txCount?.toLocaleString() || '—'}</span>
              <span>Type: {summary?.scriptType || '—'}</span>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-2xl font-bold ${riskLevel === 'critical' ? 'text-accent-red' : riskLevel === 'high' ? 'text-accent-gold' : riskLevel === 'medium' ? 'text-primary-400' : 'text-accent-green'}`}>
              {riskScore}%
            </div>
            <div className="text-[10px] text-dark-400 uppercase">Risk Score</div>
          </div>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="glass-card p-4 flex flex-col md:flex-row md:items-center gap-4">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search counterparty addresses..."
            className="w-full pl-9 pr-3 py-2 bg-dark-800/50 border border-dark-700 rounded-lg text-xs text-white placeholder:text-dark-500 focus:border-primary-500/50 focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-1.5">
          {(['all', 'inbound', 'outbound', 'both'] as const).map(dir => (
            <button
              key={dir}
              onClick={() => setDirFilter(dir)}
              className={`px-2.5 py-0.5 rounded text-[10px] font-bold capitalize transition-all cursor-pointer ${
                dirFilter === dir
                  ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                  : 'bg-dark-800 text-dark-400 border border-transparent hover:border-dark-700'
              }`}
            >
              {dir}
            </button>
          ))}
        </div>
        <span className="text-[10px] text-dark-500">{filtered.length} results</span>
      </div>

      {/* Counterparties Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-700/50">
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">Address</th>
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">Direction</th>
                <th className="text-right text-[10px] text-dark-400 font-semibold uppercase p-3">Received From</th>
                <th className="text-right text-[10px] text-dark-400 font-semibold uppercase p-3">Sent To</th>
                <th className="text-right text-[10px] text-dark-400 font-semibold uppercase p-3">Txns</th>
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">Last Seen</th>
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(cp => (
                <tr key={cp.address} className="border-b border-dark-800/50 hover:bg-dark-800/30 transition-colors">
                  <td className="p-3">
                    <code className="text-xs text-white mono">{cp.address.slice(0, 14)}…{cp.address.slice(-6)}</code>
                  </td>
                  <td className="p-3">
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase border flex items-center gap-1 w-fit ${dirColor(cp.direction)}`}>
                      {dirIcon(cp.direction)} {cp.direction}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <span className="text-xs text-accent-green font-mono">
                      {cp.totalIn > 0 ? `${(cp.totalIn / 1e8).toFixed(4)} BTC` : '—'}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <span className="text-xs text-accent-red font-mono">
                      {cp.totalOut > 0 ? `${(cp.totalOut / 1e8).toFixed(4)} BTC` : '—'}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <span className="text-xs text-white">{cp.txCount}</span>
                  </td>
                  <td className="p-3">
                    <span className="text-[10px] text-dark-400">{new Date(cp.lastSeen).toLocaleDateString()}</span>
                  </td>
                  <td className="p-3">
                    <a
                      href={`https://mempool.space/address/${cp.address}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-primary-400 hover:underline flex items-center gap-1"
                    >
                      <ExternalLink size={10} /> Explore
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filtered.length === 0 && (
          <div className="p-12 text-center text-dark-500 italic text-sm">
            {counterparties.length === 0
              ? 'No counterparties detected. Analyze a wallet to discover connected addresses.'
              : 'No counterparties match the current filter.'}
          </div>
        )}
      </div>
    </div>
  );
};
