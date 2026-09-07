import React, { useState } from 'react';
import { useInvestigationStore } from '../stores/investigation';
import { useNavStore } from '../stores';
import { 
  ShieldAlert, ShieldCheck, Activity, Clock, AlertOctagon, Terminal, 
  Search, RefreshCw, CheckCircle2, AlertTriangle, AlertCircle, Wallet, Database, Cpu, ArrowUpRight
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';

export const SocDashboardPage: React.FC = () => {
  const { activeTargetAddress, summary, transactions, alerts, riskScore, riskLevel, counterparties, evidenceItems, auditLog, isLoading, refreshTargetData } = useInvestigationStore();
  const { setPage } = useNavStore();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshTargetData();
    setIsRefreshing(false);
  };

  // Compute operational metrics from investigation data
  const criticalAlerts = alerts.filter(a => a.severity === 'critical').length;
  const highAlerts = alerts.filter(a => a.severity === 'high').length;
  const mediumAlerts = alerts.filter(a => a.severity === 'medium').length;
  const lowAlerts = alerts.filter(a => a.severity === 'low' || a.severity === 'info').length;
  const unreadAlerts = alerts.filter(a => !a.isRead).length;

  // Severity distribution for chart
  const severityData = [
    { name: 'Critical', value: criticalAlerts, color: '#ef4444' },
    { name: 'High', value: highAlerts, color: '#f59e0b' },
    { name: 'Medium', value: mediumAlerts, color: '#06b6d4' },
    { name: 'Low/Info', value: lowAlerts, color: '#22c55e' },
  ].filter(d => d.value > 0);

  // Evidence by type for bar chart
  const evidenceByType: Record<string, number> = {};
  evidenceItems.forEach(e => {
    const key = e.type.replace(/_/g, ' ');
    evidenceByType[key] = (evidenceByType[key] || 0) + 1;
  });
  const evidenceBarData = Object.entries(evidenceByType).map(([name, count]) => ({ name, count }));

  // Recent audit events
  const recentAudit = auditLog.slice(0, 8);

  const timeAgo = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert size={20} className="text-primary-400" />
            <h2 className="text-xl font-bold text-white">SOC Dashboard</h2>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Wallet size={12} className="text-primary-400" />
            <span className="text-xs text-dark-400 mono">{activeTargetAddress.slice(0, 16)}…{activeTargetAddress.slice(-8)}</span>
            <span className="text-[10px] text-dark-500">•</span>
            <span className={`text-xs font-bold ${riskLevel === 'critical' ? 'text-accent-red' : riskLevel === 'high' ? 'text-accent-gold' : 'text-primary-400'}`}>
              Risk: {riskScore}% ({riskLevel.toUpperCase()})
            </span>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          className="btn-ghost flex items-center gap-1 text-xs border border-dark-700/50"
          disabled={isRefreshing}
        >
          <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
          {isRefreshing ? 'Refreshing…' : 'Refresh Data'}
        </button>
      </div>

      {/* Stat Cards — All Active & Interactive */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {[
          { label: 'Total Alerts', value: alerts.length, icon: AlertTriangle, color: 'text-accent-gold', bg: 'bg-accent-gold/10 hover:bg-accent-gold/20 border-accent-gold/30', page: 'alerts' },
          { label: 'Unread', value: unreadAlerts, icon: AlertCircle, color: 'text-accent-red', bg: 'bg-accent-red/10 hover:bg-accent-red/20 border-accent-red/30', page: 'alerts' },
          { label: 'Counterparties', value: counterparties.length, icon: Activity, color: 'text-primary-400', bg: 'bg-primary-500/10 hover:bg-primary-500/20 border-primary-500/30', page: 'blockchain' },
          { label: 'Evidence Items', value: evidenceItems.length, icon: Database, color: 'text-accent-green', bg: 'bg-accent-green/10 hover:bg-accent-green/20 border-accent-green/30', page: 'evidence' },
          { label: 'Transactions', value: summary?.txCount || 0, icon: Terminal, color: 'text-primary-400', bg: 'bg-primary-500/10 hover:bg-primary-500/20 border-primary-500/30', page: 'blockchain' },
          { label: 'Audit Events', value: auditLog.length, icon: Clock, color: 'text-dark-300', bg: 'bg-dark-700/50 hover:bg-dark-700 border-dark-600', page: 'audit' },
        ].map(stat => (
          <div
            key={stat.label}
            onClick={() => setPage(stat.page as any)}
            className={`glass-card p-3.5 ${stat.bg} rounded-xl border transition-all cursor-pointer hover:scale-[1.03] active:scale-95 group relative overflow-hidden`}
            title={`Click to view ${stat.label}`}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <stat.icon size={12} className={stat.color} />
                <span className="text-[9px] text-dark-300 uppercase font-semibold tracking-wider group-hover:text-white transition-colors">{stat.label}</span>
              </div>
              <ArrowUpRight size={10} className="text-dark-500 group-hover:text-white transition-colors" />
            </div>
            <div className="text-xl font-bold text-white tracking-tight">{typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}</div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Alert Severity Distribution */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-bold text-white mb-4">Alert Severity Distribution</h3>
          {severityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%" cy="50%"
                  innerRadius={50} outerRadius={80}
                  dataKey="value"
                  stroke="none"
                >
                  {severityData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1a1a2e', border: '1px solid #333', borderRadius: 8, fontSize: 11 }}
                  itemStyle={{ color: '#fff' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-dark-500 text-sm italic">
              No alerts generated yet.
            </div>
          )}
          <div className="flex items-center justify-center gap-4 mt-2">
            {severityData.map(d => (
              <div key={d.name} className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                <span className="text-[10px] text-dark-400">{d.name}: {d.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Evidence by Type */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-bold text-white mb-4">Evidence by Category</h3>
          {evidenceBarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={evidenceBarData}>
                <XAxis dataKey="name" tick={{ fill: '#666', fontSize: 10 }} />
                <YAxis tick={{ fill: '#666', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ background: '#1a1a2e', border: '1px solid #333', borderRadius: 8, fontSize: 11 }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-dark-500 text-sm italic">
              No evidence items generated yet.
            </div>
          )}
        </div>
      </div>

      {/* Recent Audit Activity */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-bold text-white mb-4">Recent Investigation Activity</h3>
        <div className="space-y-2">
          {recentAudit.map(entry => (
            <div key={entry.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-dark-800/30 transition-colors">
              {entry.status === 'success' ? (
                <CheckCircle2 size={14} className="text-accent-green shrink-0" />
              ) : entry.status === 'failure' ? (
                <AlertOctagon size={14} className="text-accent-red shrink-0" />
              ) : (
                <Cpu size={14} className="text-primary-400 shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <span className="text-xs text-white">{entry.detail}</span>
              </div>
              <span className="text-[10px] text-dark-500 shrink-0">{timeAgo(entry.timestamp)}</span>
            </div>
          ))}
          {recentAudit.length === 0 && (
            <div className="text-center text-dark-500 text-sm italic py-6">
              No investigation activity yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
