import React, { useState } from 'react';
import { useInvestigationStore } from '../stores/investigation';
import { ClipboardList, Shield, Filter, Search, ShieldAlert, CheckCircle, RefreshCw, AlertOctagon, Wallet } from 'lucide-react';

const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

export const AuditPage: React.FC = () => {
  const { auditLog, activeTargetAddress, addAuditEntry } = useInvestigationStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredLogs = auditLog.filter(entry => {
    const matchesSearch = searchTerm === '' ||
      entry.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.detail.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.walletAddress.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || entry.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle size={14} className="text-accent-green" />;
      case 'failure': return <AlertOctagon size={14} className="text-accent-red" />;
      default: return <Shield size={14} className="text-primary-400" />;
    }
  };

  const getActionBadge = (action: string) => {
    const map: Record<string, string> = {
      WALLET_CHANGED: 'bg-primary-500/20 text-primary-400 border-primary-500/30',
      ANALYSIS_EXECUTED: 'bg-accent-green/20 text-accent-green border-accent-green/30',
      ANALYSIS_FAILED: 'bg-accent-red/20 text-accent-red border-accent-red/30',
      REPORT_GENERATED: 'bg-accent-gold/20 text-accent-gold border-accent-gold/30',
      EVIDENCE_ADDED: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      INVESTIGATION_STARTED: 'bg-primary-500/20 text-primary-400 border-primary-500/30',
    };
    return map[action] || 'bg-dark-700 text-dark-300 border-dark-600';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ClipboardList size={20} className="text-primary-400" />
            <h2 className="text-xl font-bold text-white">Audit Logs</h2>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Wallet size={12} className="text-primary-400" />
            <span className="text-xs text-dark-400 mono">{activeTargetAddress.slice(0, 16)}…{activeTargetAddress.slice(-8)}</span>
            <span className="text-[10px] text-dark-500">•</span>
            <span className="text-xs text-dark-400">{auditLog.length} entries</span>
          </div>
        </div>
        <button
          onClick={() => addAuditEntry('MANUAL_ENTRY', 'Manual audit log entry created by investigator')}
          className="btn-ghost flex items-center gap-1 text-xs border border-dark-700/50"
        >
          <RefreshCw size={14} /> Log Manual Entry
        </button>
      </div>

      {/* Search & Filter */}
      <div className="glass-card p-4 flex flex-col md:flex-row md:items-center gap-4">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search audit logs..."
            className="w-full pl-9 pr-3 py-2 bg-dark-800/50 border border-dark-700 rounded-lg text-xs text-white placeholder:text-dark-500 focus:border-primary-500/50 focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={12} className="text-dark-400" />
          <span className="text-xs text-dark-300">Status:</span>
          {['all', 'success', 'failure', 'info'].map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-2.5 py-0.5 rounded text-[10px] font-bold capitalize transition-all cursor-pointer ${
                statusFilter === status
                  ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                  : 'bg-dark-800 text-dark-400 border border-transparent hover:border-dark-700'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-700/50">
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">Status</th>
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">Action</th>
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">Detail</th>
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">Wallet</th>
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">Timestamp</th>
                <th className="text-left text-[10px] text-dark-400 font-semibold uppercase p-3">User</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((entry) => (
                <tr key={entry.id} className="border-b border-dark-800/50 hover:bg-dark-800/30 transition-colors">
                  <td className="p-3">
                    {getStatusIcon(entry.status)}
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${getActionBadge(entry.action)}`}>
                      {entry.action}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-xs text-white">{entry.detail}</span>
                  </td>
                  <td className="p-3">
                    <code className="text-[10px] text-dark-400 mono">{entry.walletAddress.slice(0, 12)}…</code>
                  </td>
                  <td className="p-3">
                    <span className="text-[10px] text-dark-400">{timeAgo(entry.timestamp)}</span>
                  </td>
                  <td className="p-3">
                    <span className="text-[10px] text-dark-400">{entry.username}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredLogs.length === 0 && (
          <div className="p-12 text-center text-dark-500 italic text-sm">
            {auditLog.length === 0
              ? 'No audit log entries yet. Analyze a wallet to start generating audit trail.'
              : 'No entries match the current filter.'}
          </div>
        )}
      </div>
    </div>
  );
};
